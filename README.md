# Checkout Payment API Automation

<p align="center">
  <img src="MyDigiPay.png" width="30" alt="Digipay Logo"><strong>  API Regression Test Suite for Digipay Checkout Payment Methods</strong>
  <br>
  Automated validation of <code>GET /payment/</code> using Python, Pytest and Playwright.
</p>
---

## 1. Project Overview

This project provides an API regression test suite for validating Digipay checkout payment methods.

The main objective is to verify API response structure, data integrity, payment eligibility, and business rules across different payment scenarios.

The suite covers both successful and invalid responses through isolated test data, ensuring deterministic and repeatable test execution without depending on a live environment.

## 2. Test Approach

**Approach A — Mockoon**

Tests call a real HTTP endpoint with Playwright `APIRequestContext`. Each `CellNumber` is a query rule in `mockoon/checkout-payment.json`. No live Digipay environment.

Local: Mockoon Desktop. CI: `@mockoon/cli` starts `mockoon/checkout-payment.json` before pytest.

## 3. Test Analysis & Design



### 3.1 Requirement Analysis

The API requirements were analyzed and translated into seven validation rules (R1–R7).

The analysis focused on:

- Required fields and expected data types.
- Supported payment methods (`online`, `wallet`, `bnpl`).
- Payment eligibility and active options.
- Default payment method constraints.
- Price type validation.
- Wallet-specific requirements.
- HTTP status and response body consistency.

These rules are implemented independently in the `validators/` package to separate business validation from API communication.

### 3.2 Test Design Techniques

The test scenarios were designed using the following testing approaches:


| Test Type                    | Coverage                                                   |
| ---------------------------- | ---------------------------------------------------------- |
| Positive Testing             | Valid payment methods and eligible payment options         |
| Negative Testing             | Missing fields, invalid types and business rule violations |
| Boundary & Edge Case Testing | Zero credit, empty options and multiple default methods    |
| API Error Handling           | HTTP 500 and inconsistent response body status             |




### 3.3 Scenario Execution Flow

Each scenario follows a consistent Given / When / Then structure:

1. **Given:** Select a customer using a predefined `CellNumber` fixture.
2. **When:** Send an HTTP GET request to `/payment/` using Playwright.
3. **Then:** Validate HTTP status, response structure, data types and business rules.
4. **Report:** On failure, log HTTP request and response.

Each fixture represents an isolated test condition, allowing scenarios to run independently and consistently.

### 3.4 Test Organization

The suite uses Gherkin feature files with `pytest-bdd` step definitions.

This approach separates:

- Business-readable test scenarios.
- API request execution.
- Response and business rule validation.
- Test data and reporting.

This separation improves maintainability and makes it easier to extend the suite with additional scenarios and validation rules.

## 4. Installation & Execution



### Requirements

- Python (see `requirements.txt`)
- Mockoon Desktop **or** `@mockoon/cli` (must be running on port 8080 before pytest)



### Setup

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
python -m playwright install

# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```



### Mock Server With Mockoon

Mockoon is used to simulate the Payment API, keeping mock service configuration separate from the test automation code.
Mockoon must be up on port **8080** before pytest. Two ways:

1. **Mockoon Desktop (Windows GUI)**
2. **CLI** (no Desktop install)

**1. Desktop (download from [https://mockoon.com/download/](https://mockoon.com/download/))**

1. Open Mockoon Desktop.
2. Go to File → Open local environment.
3. Select mockoon/checkout-payment.json.
4. Click Start local server ▶.

```bash
pytest
pytest -m smoke
pytest -m regression
(Or pytest -m "regression and not smoke")
```

After you change routes, save/export so `mockoon/checkout-payment.json` is what CI starts.

**2. CLI (no GUI)**

Needs [Node.js](https://nodejs.org/) (`npx`). Split the terminal:

Tab 1 — leave this running:

```bash
npx @mockoon/cli start --data mockoon/checkout-payment.json --port 8080
```

Optional: add `--log-transaction` at the end to print full request/response JSON in that tab:

```bash
npx @mockoon/cli start --data mockoon/checkout-payment.json --port 8080 --log-transaction
```

Tab 2:

```bash
pytest
```

Optional check: `http://127.0.0.1:8080/payment/?CellNumber=09121111111`

## 5. Scenarios (`CellNumber`)

Payloads live in Mockoon. The suite only sends `GET /payment/?CellNumber=…`.


| CellNumber  | Scenario                          |
| ----------- | --------------------------------- |
| 09121111111 | S01 Happy path                    |
| 09122222222 | S02 BNPL blocked                  |
| 09123333333 | S03 Zero credit                   |
| 09124444444 | S04 Inactive option               |
| 09125555555 | S05 Multiple defaults             |
| 09126666666 | S06 Missing required fields       |
| 09127777777 | S07 Invalid types                 |
| 09128888888 | S08 HTTP 500                      |
| 09129999999 | S09 Body status ≠ 200             |
| 09120000009 | S10 Missing wallet `source_id`    |
| 09120000010 | S11 Invalid `price_type`          |
| 09120000011 | S12 Clickable BNPL, empty options |




## 6. Project Structure


| Directory / File                | Responsibility                                             |
| ------------------------------- | ---------------------------------------------------------- |
| `features/`                     | Gherkin feature files and business scenarios               |
| `steps/`                        | Given / When / Then step definitions                       |
| `apis/`                         | HTTP communication through Playwright                      |
| `validators/`                   | Schema, data type and business rule validations (R1–R7)    |
| `mockoon/checkout-payment.json` | Mockoon environment (edit in Desktop; CI starts this file) |
| `reports/`                      | HTML and Allure test reports                               |
| `.github/workflows/`            | GitHub Actions CI configuration                            |




## 7. HTML Test Report

Each pytest execution generates a self-contained HTML report:

`reports/report.html`

The report includes:

- Execution summary and pass/fail/skip counts.
- Environment and endpoint information.
- Expandable test result rows.
- Failed tests include HTTP request and response.



### Report Customization

`pytest-html` is configured through `pytest.ini` with `--self-contained-html`.

Digipay styling is applied through:

`reports/assets/report.css`

The report uses the Digipay brand blue (`#0000FF`) and IBM Plex typography.

If the logo is replaced, regenerate the embedded CSS:

```bash
python reports/assets/_build_css.py
pytest
```

The generated HTML is a static snapshot of the test execution and can be opened directly in a browser without a web server.

## 8. Allure Report

The project also generates Allure results for richer test execution analysis.

Results directory:

`reports/allure-results/`

### Open Interactive Report

Requirements: Java 21+ and Allure CLI.

```bash
npm install -g allure-commandline
allure serve reports/allure-results
```



### Generate Static HTML

```bash
allure generate reports/allure-results -o reports/allure-report --clean
```

Open:

`reports/allure-report/index.html`

Each test includes:

- Epic: `Digipay`
- Feature: Gherkin feature file
- Story: Scenario name
- Request / Response attachment
- Response JSON attachment
- Environment metadata

Use the standard HTML report for a lightweight execution summary and Allure for more detailed test analysis.

## 9. Assumptions & Validation Rules

The following assumptions were used during test implementation:

- `GET /payment/?CellNumber=` is sufficient to select the customer payload.
- Supported `type` values are lowercase: `online`, `wallet`, `bnpl`.
- `price_type` is case-sensitive: `CASH_PRICE` / `CREDIT_PRICE`.
- Boolean values are rejected where integers are required (`True` is not a valid `id`).
- R6 is evaluated only among eligible options and only when at least one eligible option exists.
- Selectable means `is_clickable is True` (R2).
- Eligible means `is_active is True` and `credit > 0` (R5).



## 10. Continuous Integration (CI)

GitHub Actions executes the regression suite automatically.

Workflow:

`.github/workflows/ci.yml`

Execution environment:

- Ubuntu 24.04 (`ubuntu-24.04`)
- `@mockoon/cli` serves `mockoon/checkout-payment.json` on port 8080
- Python, Playwright, pytest

The workflow uploads the generated HTML report and Allure report as CI artifacts.

The runner is pinned to Ubuntu 24.04 because Playwright 1.55 does not provide a Chromium build for Ubuntu 26.04 (`ubuntu-latest`).

---
**Digipay Checkout Payment API – Automated Regression Suite**  
Python · Pytest · Playwright · pytest-bdd · Mockoon · Allure · GitHub Actions
