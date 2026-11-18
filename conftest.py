from __future__ import annotations

import os
import urllib.error
import urllib.request
from html import escape
from pathlib import Path

import allure
import pytest
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from pytest_metadata.plugin import metadata_key

from apis.payment_api import PaymentApi
from validators.payment_validator import PaymentValidator

load_dotenv(Path(__file__).resolve().parent / ".env")


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.getenv("BASE_URL", "http://127.0.0.1:8080").rstrip("/")


@pytest.fixture(scope="session", autouse=True)
def require_mockoon(base_url):
    url = f"{base_url}/payment/?CellNumber=09121111111"
    try:
        urllib.request.urlopen(url, timeout=3)
    except urllib.error.URLError as error:
        pytest.exit(
            f"Mockoon is not running at {url}. "
            "Desktop: File → Open environment → mockoon/checkout-payment.json, then Start. "
            "CLI: npx @mockoon/cli start --data mockoon/checkout-payment.json --port 8080. "
            f"Details: {error}",
            returncode=1,
        )
    yield


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
def payment_api(request, request_context, base_url) -> PaymentApi:
    api = PaymentApi(request_context, base_url)
    request.node.payment_api_client = api
    return api


@pytest.fixture
def validator(request) -> PaymentValidator:
    instance = PaymentValidator(node=request.node)
    request.node.payment_validator = instance
    return instance


def _ensure_progress(node) -> list:
    progress = getattr(node, "progress_log", None)
    if progress is None:
        progress = []
        node.progress_log = progress
    return progress


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


def pytest_bdd_after_step(request, feature, scenario, step, step_func, step_func_args):
    current = getattr(request.node, "current_step", None)
    if isinstance(current, dict):
        current["passed"] = True


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
                "Approach=A Mockoon + JSON fixtures",
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
    config.stash[metadata_key]["Approach"] = "A — Mockoon + JSON fixtures"
    config.stash[metadata_key]["Mock"] = "Mockoon"
    config.stash[metadata_key]["Client"] = "Playwright APIRequestContext"


def pytest_html_report_title(report):
    report.title = "Digipay · Checkout Payment API"


def pytest_html_results_table_header(cells):
    cells[:] = [cell for cell in cells if "Links" not in cell]


def pytest_html_results_table_row(report, cells):
    cells[:] = [cell for cell in cells if 'class="col-links"' not in cell]


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
            "Passed tests log each rule that passed. "
            "Failed tests include the HTTP request/response."
            "</p>"
        ]
    )


def _format_progress(item, error: str = "") -> str:
    progress = getattr(item, "progress_log", None) or []
    if progress and isinstance(progress[0], dict):
        blocks = []
        for step in progress:
            status = "passed" if step.get("passed") else "failed"
            blocks.append(
                f"<span class='log-step'>{escape(step['keyword'])} {escape(step['name'])} {status}</span>"
            )
            for rule in step.get("rules", []):
                blocks.append(f"<span class='log-rule'>    {escape(rule)}</span>")
        if error:
            blocks.append(f"<span class='log-fail'>    failed {escape(error)}</span>")
        return "<pre class='http-dump'>" + "\n".join(blocks) + "</pre>"

    validator = getattr(item, "payment_validator", None)
    lines = list(validator.rule_log) if validator and validator.rule_log else []
    if error:
        lines.append(f"failed {error}")
    return "<pre class='http-dump'>" + escape("\n".join(lines)) + "</pre>"


def _http_log(item) -> str:
    api = getattr(item, "payment_api_client", None)
    if api is None or api.last_call is None:
        return ""
    return api.last_call.as_log()


def _html_extra(item, report, markup: str) -> None:
    pytest_html = item.config.pluginmanager.getplugin("html")
    if pytest_html is None or not markup:
        return
    extras = getattr(report, "extras", [])
    extras.append(pytest_html.extras.html(markup))
    report.extras = extras


def _exception_line(call) -> str:
    if call.excinfo is None:
        return ""
    exc_type = call.excinfo.type
    return f"{exc_type.__module__}.{exc_type.__qualname__}: {call.excinfo.value}"


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)
    if report.when not in ("setup", "call"):
        return

    if report.passed and report.when == "call":
        _html_extra(item, report, _format_progress(item))
        return

    if report.failed:
        error = _exception_line(call)
        _html_extra(item, report, _format_progress(item, error))
        http_log = _http_log(item)
        if http_log:
            report.longrepr = f"{report.longrepr}\n\nRequest / response:\n{http_log}"
