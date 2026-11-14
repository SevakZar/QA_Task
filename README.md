# Checkout Payment API automation

API regression suite for Digipay checkout payment methods (`GET /payment/`).

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

HTML report: `reports/report.html`.

## CellNumber fixtures

| CellNumber  | Scenario |
|-------------|----------|
| 09121111111 | S1 happy path |
| 09122222222 | S2 BNPL blocked |
| 09123333333 | S3 credit = 0 |
| 09124444444 | S4 `is_active = false` |
| 09125555555 | S5 two eligible defaults |
| 09126666666 | S6 missing `type` / `title` |
| 09127777777 | S7 wrong types |
| 09128888888 | S8 HTTP 500 |
| 09129999999 | S8 body `status != 200` |
| 09120000009 | S9 wallet without `source_id` |
| 09120000010 | S10 invalid `price_type` |
| 09120000011 | S11 clickable BNPL, empty options |

## Layout

- `features/` — Gherkin only (no HTTP or JSON)
- `steps/test_checkout.py` — Given / When / Then (pytest collects `test_*.py`)
- `apis/` — Playwright client
- `validators/` — schema, types, rules R1–R7
- `testdata/` — response fixtures
- `mock_server/` — fake `GET /payment/`
- Failures name the rule, method/option, and actual value; request/response are logged on failed tests

## Assumptions

- `GET /payment/?CellNumber=` is enough to select the customer payload.
- `type` is lowercase `online` | `wallet` | `bnpl`.
- `price_type` is case-sensitive (`CASH_PRICE` / `CREDIT_PRICE`).
- `bool` is rejected where `int` is required (`True` is not a valid `id`).
- R6 is evaluated only among eligible options, and only when at least one eligible option exists.
- Selectable means `is_clickable is True` (R2). Eligible option means `is_active is True` and `credit > 0` (R5).

## CI

`.github/workflows/ci.yml` runs pytest on `ubuntu-24.04` and uploads `reports/report.html`. The runner is pinned because Playwright 1.55 does not ship Chromium for Ubuntu 26.04 (`ubuntu-latest`).
