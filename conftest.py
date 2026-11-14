from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import allure
import pytest
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from pytest_metadata.plugin import metadata_key

from apis.payment_api import PaymentApi
from mock_server.server import MockServer
from validators.payment_validator import PaymentValidator

load_dotenv()

LOGGER = logging.getLogger("checkout-api")


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.getenv("BASE_URL", "http://127.0.0.1:8080")


@pytest.fixture(scope="session")
def mock_port(base_url) -> int:
    return int(os.getenv("MOCK_PORT", "8080"))


@pytest.fixture(scope="session", autouse=True)
def mock_server(mock_port):
    server = MockServer(port=mock_port)
    server.start()
    yield server
    server.stop()


@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def request_context(playwright_instance, base_url):
    context = playwright_instance.request.new_context(base_url=base_url)
    yield context
    context.dispose()


@pytest.fixture
def payment_api(request_context, base_url) -> PaymentApi:
    return PaymentApi(request_context, base_url)


@pytest.fixture
def validator() -> PaymentValidator:
    return PaymentValidator()


@pytest.fixture(autouse=True)
def allure_http_attachment(payment_api):
    yield
    call = payment_api.last_call
    if call is None:
        return
    allure.attach(
        call.as_log(),
        name="Request / Response",
        attachment_type=allure.attachment_type.TEXT,
    )
    if isinstance(call.body, dict):
        allure.attach(
            json.dumps(call.body, indent=2, ensure_ascii=False),
            name="Response JSON",
            attachment_type=allure.attachment_type.JSON,
        )


def pytest_bdd_before_scenario(request, feature, scenario):
    allure.dynamic.epic("Digipay")
    allure.dynamic.feature(feature.name)
    allure.dynamic.story(scenario.name)
    allure.dynamic.suite("Checkout Payment API")


def pytest_sessionfinish(session, exitstatus):
    results_dir = session.config.getoption("--alluredir")
    if not results_dir:
        return
    path = Path(results_dir)
    path.mkdir(parents=True, exist_ok=True)
    (path / "environment.properties").write_text(
        "\n".join(
            [
                "Product=Digipay Checkout",
                "Suite=Checkout Payment API",
                "Endpoint=GET /payment/",
                "Approach=A local mock server + JSON fixtures",
                "Client=Playwright APIRequestContext",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def pytest_configure(config):
    config.stash[metadata_key]["Product"] = "Digipay Checkout"
    config.stash[metadata_key]["Suite"] = "Checkout Payment API"
    config.stash[metadata_key]["Endpoint"] = "GET /payment/"
    config.stash[metadata_key]["Approach"] = "A — local mock server + JSON fixtures"
    config.stash[metadata_key]["Client"] = "Playwright APIRequestContext"


def pytest_html_report_title(report):
    report.title = "Digipay · Checkout Payment API"


def pytest_html_results_summary(prefix, summary, postfix, session):
    prefix.extend(
        [
            "<div class='digipay-banner'>"
            "<span class='digipay-chip'>Practical task</span>"
            "<span>Software QA Engineer · schema, business rules R1–R7, negative cases</span>"
            "</div>"
        ]
    )
    postfix.extend(
        [
            "<p class='digipay-footer-note'>"
            "Expand a row for Captured log call and the Request / Response extra. "
            "Failed tests also include the rule id, method/option, and actual value."
            "</p>"
        ]
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return
    api = item.funcargs.get("payment_api")
    if api is None or api.last_call is None:
        return
    http_log = api.last_call.as_log()
    pytest_html = item.config.pluginmanager.getplugin("html")
    extras = getattr(report, "extras", [])
    if pytest_html is not None:
        extras.append(pytest_html.extras.text(http_log, name="Request / Response"))
        report.extras = extras
    if report.failed:
        LOGGER.error("Failed test diagnostics\n%s", http_log)
        report.longrepr = f"{report.longrepr}\n\nRequest / response:\n{http_log}"
