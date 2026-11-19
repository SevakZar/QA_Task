from __future__ import annotations

import os
import urllib.error
import urllib.request
from pathlib import Path

import allure
import pytest
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from apis.payment_api import PaymentApi
from validators.payment_validator import PaymentValidator


load_dotenv(Path(__file__).parent / ".env")


# Configuration

@pytest.fixture(scope="session")
def base_url() -> str:
    return os.getenv(
        "BASE_URL",
        "http://127.0.0.1:8080"
    ).rstrip("/")


# Mock Server

@pytest.fixture(scope="session", autouse=True)
def require_mockoon(base_url):
    url = f"{base_url}/payment/?CellNumber=09121111111"

    try:
        with urllib.request.urlopen(url, timeout=3):
            pass

    except urllib.error.URLError as error:
        pytest.exit(
            f"Mockoon is not running at {url}. "
            "Start mockoon/checkout-payment.json first. "
            f"Details: {error}",
            returncode=1,
        )


# Playwright

@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def request_context(playwright_instance, base_url):
    context = playwright_instance.request.new_context(
        base_url=base_url
    )

    yield context

    context.dispose()


# API Client

@pytest.fixture
def payment_api(request, request_context, base_url):
    api = PaymentApi(request_context, base_url)
    request.node.payment_api = api
    return api


# Validator

@pytest.fixture
def validator(request):
    return PaymentValidator(node=request.node)


def _ensure_progress(node) -> list:
    progress = getattr(node, "progress_log", None)
    if progress is None:
        progress = []
        node.progress_log = progress
    return progress


def _attach_http(item):
    api = getattr(item, "payment_api", None)
    if api is None or api.last_call is None:
        return
    if getattr(item, "_http_attached", False):
        return
    item._http_attached = True
    allure.attach(
        "Request / response:\n" + api.last_call.as_log(),
        name="Request / response",
        attachment_type=allure.attachment_type.TEXT,
    )

# Allure Metadata

def pytest_bdd_before_scenario(request, feature, scenario):
    _ensure_progress(request.node).clear()
    request.node.current_step = None
    allure.dynamic.epic("Digipay")
    allure.dynamic.feature(feature.name)
    allure.dynamic.story(scenario.name)
    allure.dynamic.suite("Checkout Payment API")


def pytest_bdd_before_step(request, feature, scenario, step, step_func):
    current = {
        "keyword": step.keyword.strip(),
        "name": step.name,
        "passed": False,
        "rules": [],
    }
    request.node.current_step = current
    _ensure_progress(request.node).append(current)
    context = allure.step(f"{current['keyword']} {current['name']}")
    request.node._allure_step = context
    context.__enter__()


def pytest_bdd_after_step(request, feature, scenario, step, step_func, step_func_args):
    current = getattr(request.node, "current_step", None)
    if isinstance(current, dict):
        current["passed"] = True
        for rule in current.get("rules", []):
            with allure.step(rule):
                pass
    context = getattr(request.node, "_allure_step", None)
    if context is not None:
        request.node._allure_step = None
        context.__exit__(None, None, None)
    _attach_http(request.node)


def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    current = getattr(request.node, "current_step", None)
    if isinstance(current, dict):
        for rule in current.get("rules", []):
            with allure.step(rule):
                pass
        with allure.step(f"failed {exception}"):
            pass
    context = getattr(request.node, "_allure_step", None)
    if context is not None:
        request.node._allure_step = None
        context.__exit__(type(exception), exception, exception.__traceback__)
    _attach_http(request.node)


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if not report.failed:
        return
    api = getattr(item, "payment_api", None)
    if api is None or api.last_call is None:
        return
    report.longrepr = f"{report.longrepr}\n\nRequest / response:\n{api.last_call.as_log()}"
