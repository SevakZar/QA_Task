# Checkout Payment API automation

<p align="left">
  <img src="MyDigiPay.png" width="30" alt="Digipay"> API regression suite for Digipay checkout payment methods (`GET /payment/`).
</p>

## Problem analysis

Checkout renders payment methods from one aggregator endpoint (`online`, `wallet`, `bnpl`). A bad response can show a non-selectable method as selectable, or mark an invalid BNPL plan as default.

In scope: response contract (schema/types/required fields), business rules R1–R7, negative/edge HTTP and body cases, actionable failure output.

Out of scope: UI, real payment (OTP/bank), deep price correctness.

## Approach

**A — local mock server** + JSON fixtures under `testdata/`.

- Tests hit a real HTTP endpoint via Playwright `APIRequestContext`.
- Mock maps `CellNumber` → fixture so each scenario is deterministic.
- No live Digipay environment.

Approach B (JSON-only, no HTTP) was skipped: the brief requires Playwright request testing, and S08 needs a real non-200 HTTP status.

## Test design

| Aspect | Choice |
|--------|--------|
| Style | BDD (Gherkin) — scenarios readable without code |
| Layers | Feature has no HTTP/JSON; client in `apis/`; rules in `validators/` |
| Data | One fixture per scenario; positive vs negative folders |
| Coverage | S01–S08 required + S09–S12 for R3/R7/R4 extras |
| Assertions | Positive: full validate + eligibility checks. Negative: expect a named rule (`R1`…`R7` / `HTTP` / `BODY.status`) |
| Diagnostics | Failures include rule, method/option, actual value; request/response logged every run |

Flow per scenario:

1. Given a `CellNumber`
2. When `GET /payment/?CellNumber=…`
3. Then success check and/or rule validation

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

Mock starts automatically for the pytest session (`BASE_URL`, default `http://127.0.0.1:8080`).

Standalone mock (optional):

```bash
python -m mock_server.server --port 8080
```

## Layout

| Path | Role |
|------|------|
| `features/` | Gherkin only |
| `steps/test_checkout.py` | Given / When / Then |
| `apis/` | Playwright HTTP client |
| `validators/` | Contract + R1–R7 |
| `testdata/01_positive/` | Valid / eligibility fixtures |
| `testdata/02_negative/` | Contract / rule / HTTP failures |
| `mock_server/` | Fake `GET /payment/` |
| `conftest.py` | Fixtures, mock lifecycle, reports |
| `reports/` | pytest-html + Allure output |

## CellNumber → fixture

| CellNumber | Scenario | Fixture |
|------------|----------|---------|
| 09121111111 | S01 happy path | `01_positive/S01_happy_path.json` |
| 09122222222 | S02 BNPL blocked | `01_positive/S02_bnpl_blocked.json` |
| 09123333333 | S03 credit = 0 | `01_positive/S03_insufficient_credit.json` |
| 09124444444 | S04 inactive option | `01_positive/S04_non_active_option.json` |
| 09125555555 | S05 two defaults | `02_negative/S05_invalid_default.json` |
| 09126666666 | S06 missing fields | `02_negative/S06_missing_required_field.json` |
| 09127777777 | S07 wrong types | `02_negative/S07_wrong_types.json` |
| 09128888888 | S08 HTTP 500 | `02_negative/S09_http_500.json` |
| 09129999999 | S09 body status ≠ 200 | `02_negative/S08_body_status.json` |
| 09120000009 | S10 missing `source_id` | `02_negative/S10_missing_source_id.json` |
| 09120000010 | S11 invalid `price_type` | `02_negative/S11_invalid_price_type.json` |
| 09120000011 | S12 empty options + clickable | `02_negative/S12_empty_options_clickable.json` |

## Reports

**pytest-html** — `reports/report.html` after every run (Digipay blue + logo). Expand a row for request/response and failure detail. Good for PR screenshots.

**Allure** — results in `reports/allure-results/` on every `pytest`. Needs Java 21+ and Allure CLI:

```bash
npm install -g allure-commandline
allure serve reports/allure-results
# or
allure generate reports/allure-results -o reports/allure-report --clean
```

CI uploads both reports. Logo CSS rebuild if PNG changes: `python reports/assets/_build_css.py` then `pytest`.

## Assumptions

- `CellNumber` alone selects the customer payload.
- `type`: lowercase `online` | `wallet` | `bnpl`.
- `price_type`: case-sensitive `CASH_PRICE` / `CREDIT_PRICE`.
- `bool` is not a valid `int` (e.g. for `id`).
- R6: exactly one `is_default=true` among **eligible** options, only if any eligible option exists.
- Selectable = `is_clickable is True` (R2). Eligible option = `is_active is True` and `credit > 0` (R5).

## CI

`.github/workflows/ci.yml` runs on `ubuntu-24.04` (Playwright 1.55 has no Chromium for Ubuntu 26.04 / `ubuntu-latest`) and uploads `report.html` + Allure HTML.
