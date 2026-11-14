from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from apis.payment_api import PaymentApi
from mock_server.server import MockServer
from validators.payment_validator import PaymentValidator

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
LOGGER = logging.getLogger("checkout-api")

ROOT = Path(__file__).resolve().parent


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
