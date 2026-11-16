# Checkout Payment API automation
<p align="left">
  <img src="MyDigiPay.png" width="30" alt="Test Execution"> API regression suite for Digipay checkout payment methods (`GET /payment/`).
</p>


## Approach

**A — local mock server**, backed by JSON fixtures in `testdata/`.

Tests call a real HTTP endpoint through Playwright `APIRequestContext`. The mock maps `CellNumber` to a fixture so each scenario is deterministic and no live environment is required.

Approach B (JSON-only, no HTTP) was not used: the brief asks for Playwright request testing, and HTTP status handling (S8) needs an actual response.

## Install and run

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
python -m playwright install
copy .env.example .env   # or: cp .env.example .env
pytest
```

The mock server starts automatically for the pytest session on `BASE_URL` (default `http://127.0.0.1:8080`).

Standalone mock (optional):

```bash
python -m mock_server.server --port 8080
```

## HTML report

Each `pytest` run writes a self-contained file: `reports/report.html` (also uploaded by GitHub Actions).

### How it works

`pytest-html` hooks into the pytest run. `pytest.ini` points `--html` at `reports/report.html`, inlines CSS/JS with `--self-contained-html`, and applies Digipay styling from `reports/assets/report.css`. The header uses `MyDigiPay.png` and brand blue `#0000FF` sampled from that file. If you replace the PNG, run `python reports/assets/_build_css.py` then `pytest` so the logo is embedded again. `conftest.py` sets the title, environment metadata, summary blurb, and attaches the last HTTP call to every test row.

Open the file in a browser after a run. You do not need a server.

### What you get

| Feature | Where |
|---|---|
| Digipay logo (`MyDigiPay.png`), brand blue `#0000FF`, IBM Plex | Header / footer (`report.css`) |
| Environment (product, endpoint, approach, Python) | Top table |
| Pass / fail / skip counts and filters | Summary |
| Expandable rows | Results table |
| Request URL, query, status, headers, body | Expanded row (`<pre>`) + **Captured log call** |
| Rule id, method/option, actual value | Failure traceback on red rows |

This is a static snapshot of one run, not a live GUI like Cypress.

## Allure report

Allure is the richer report many QA teams use (suites, attachments, environment, filters). This suite writes Allure results on every `pytest` run.

```bash
pip install -r requirements.txt
pytest
```

Results: `reports/allure-results/`. To open the UI you need **Java 21+** and the Allure CLI:

```bash
npm install -g allure-commandline
allure serve reports/allure-results
```

Static HTML (same as CI):

```bash
allure generate reports/allure-results -o reports/allure-report --clean
```

Then open `reports/allure-report/index.html`.

Each test gets:

- Epic `Digipay`, feature from the Gherkin file, story = scenario name
- **Request / Response** text attachment
- **Response JSON** attachment
- Environment: product, endpoint, mock approach

Keep `reports/report.html` for a single-file screenshot. Use Allure when you want the standard QA report UI.

## CellNumber fixtures

| CellNumber  | Scenario | Fixture |
|-------------|----------|---------|
| 09121111111 | S01 happy path | `testdata/01_positive/S01_happy_path.json` |
| 09122222222 | S02 BNPL blocked | `testdata/01_positive/S02_bnpl_blocked.json` |
| 09123333333 | S03 credit = 0 | `testdata/01_positive/S03_insufficient_credit.json` |
| 09124444444 | S04 `is_active = false` | `testdata/01_positive/S04_non_active_option.json` |
| 09125555555 | S05 two eligible defaults | `testdata/02_negative/S05_invalid_default.json` |
| 09126666666 | S06 missing `type` / `title` | `testdata/02_negative/S06_missing_required_field.json` |
| 09127777777 | S07 wrong types | `testdata/02_negative/S07_wrong_types.json` |
| 09128888888 | S08 HTTP 500 | `testdata/02_negative/S09_http_500.json` |
| 09129999999 | S09 body `status != 200` | `testdata/02_negative/S08_body_status.json` |
| 09120000009 | S10 wallet without `source_id` | `testdata/02_negative/S10_missing_source_id.json` |
| 09120000010 | S11 invalid `price_type` | `testdata/02_negative/S11_invalid_price_type.json` |
| 09120000011 | S12 clickable BNPL, empty options | `testdata/02_negative/S12_empty_options_clickable.json` |

## Layout

- `features/` — Gherkin only (no HTTP or JSON)
- `steps/test_checkout.py` — Given / When / Then (pytest collects `test_*.py`)
- `apis/` — Playwright client
- `validators/` — schema, types, rules R1–R7
- `testdata/01_positive/` and `testdata/02_negative/` — response fixtures (`S01`–`S12`)
- `mock_server/` — fake `GET /payment/`
- Failures name the rule, method/option, and actual value; every test logs request/response

## Assumptions

- `GET /payment/?CellNumber=` is enough to select the customer payload.
- `type` is lowercase `online` | `wallet` | `bnpl`.
- `price_type` is case-sensitive (`CASH_PRICE` / `CREDIT_PRICE`).
- `bool` is rejected where `int` is required (`True` is not a valid `id`).
- R6 is evaluated only among eligible options, and only when at least one eligible option exists.
- Selectable means `is_clickable is True` (R2). Eligible option means `is_active is True` and `credit > 0` (R5).

## CI

`.github/workflows/ci.yml` runs pytest on `ubuntu-24.04` and uploads `reports/report.html` plus `reports/allure-report`. The runner is pinned because Playwright 1.55 does not ship Chromium for Ubuntu 26.04 (`ubuntu-latest`).
