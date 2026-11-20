# Performance tests (`GET /payment/`)

k6 scripts only. They are **not** part of pytest. Mockoon must already be running on `BASE_URL` (default `http://127.0.0.1:8080`).

Same request in every script:

`GET /payment/?CellNumber=09121111111` (S01 happy path)

## Baseline

Need a number to compare later? Run **smoke** (or load) and keep the terminal summary (`p95`, error rate). That run is the baseline. There is no extra baseline file.

## Scripts

| File | Kind | Profile |
| --- | --- | --- |
| `payment_smoke_test.js` | Smoke | 1 VU, 10s — is the endpoint and script alive? |
| `payment_load_test.js` | Load | steady VUs (see the file) for 30s — expected traffic |
| `payment_spike_test.js` | Spike | 2 → 20 → 2 VUs — sudden burst |
| `payment_stress_test.js` | Stress | ramp 5 → 10 → 20 → 0 — push past load |

Each iteration sleeps 1s. Checks: HTTP 200, `body.status === 200`, `payment_methods` is an array.

Fail if error rate ≥ 1%, p95 ≥ 1s, or checks drop below 99%.

## Run

k6 has no `pytest`-style “run the folder”. One command runs **one** script. All four, **one after another** (stops on the first failure):

```bash
k6 run performance/payment_smoke_test.js && k6 run performance/payment_load_test.js && k6 run performance/payment_spike_test.js && k6 run performance/payment_stress_test.js
```

Or one at a time:

```bash
k6 run performance/payment_smoke_test.js
k6 run performance/payment_load_test.js
k6 run performance/payment_spike_test.js
k6 run performance/payment_stress_test.js
```

Optional:

```bash
k6 run -e BASE_URL=http://127.0.0.1:8080 -e CELL_NUMBER=09121111111 performance/payment_smoke_test.js
```

Each run writes a basic HTML file (and refreshes the index):

- `reports/performance-report/index.html`
- `reports/performance-report/smoke.html` + `smoke.json`
- `reports/performance-report/load.html` + `load.json`
- `reports/performance-report/spike.html` + `spike.json`
- `reports/performance-report/stress.html` + `stress.json`

Each HTML page has small charts (duration bars, check rate, HTTP ok/fail), the k6-style **terminal dump**, thresholds, checks, and all metrics. The same terminal text is printed in the console. JSON is the full end-of-test object.

These numbers are **local Mockoon**, not Digipay production capacity.
