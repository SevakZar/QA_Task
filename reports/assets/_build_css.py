from pathlib import Path
import base64

root = Path(__file__).resolve().parents[2]
logo = (root / "MyDigiPay.png").read_bytes()
b64 = base64.b64encode(logo).decode("ascii")

css = """@import url("https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap");

:root {
  --dp-blue: #0000FF;
  --dp-blue-soft: #e8e8ff;
  --dp-paper: #f5f6fb;
  --dp-ink: #1b1b2f;
  --dp-muted: #5c5c78;
  --dp-line: #d8d8ee;
  --dp-white: #ffffff;
  --dp-pass: #1f7a3a;
  --dp-fail: #d64545;
}

html {
  background: var(--dp-blue);
}

body {
  font-family: "IBM Plex Sans", "Segoe UI", Helvetica, Arial, sans-serif;
  font-size: 14px;
  color: var(--dp-ink);
  background: var(--dp-paper);
  margin: 0;
  min-width: 800px;
}

h1#title {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 0;
  padding: 24px 40px 8px;
  background: var(--dp-blue);
  color: var(--dp-white);
  font-size: 26px;
  font-weight: 700;
  letter-spacing: 0.01em;
}

h1#title::before {
  content: "";
  width: 48px;
  height: 48px;
  flex: 0 0 48px;
  border-radius: 12px;
  background: var(--dp-white) url("data:image/png;base64,__LOGO__") center / 48px 48px no-repeat;
  box-shadow: 0 0 0 2px var(--dp-white);
}

h1#title::after {
  content: "API AUTOMATION · CHECKOUT";
  margin-left: auto;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.14em;
  color: var(--dp-white);
  opacity: 0.9;
}

body > p:first-of-type {
  margin: 0;
  padding: 4px 40px 22px;
  background: var(--dp-blue);
  color: #d6d6ff;
  border-bottom: 3px solid var(--dp-white);
  font-size: 13px;
}

body > p:first-of-type a {
  color: var(--dp-white);
  text-decoration: underline;
  font-weight: 600;
}

h2 {
  font-size: 15px;
  font-weight: 600;
  color: var(--dp-blue);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

p,
a {
  color: var(--dp-ink);
}

a {
  color: var(--dp-blue);
}

#environment-header,
.summary,
#environment,
#results-table {
  margin-left: 40px;
  margin-right: 40px;
}

#environment-header {
  margin-top: 28px;
}

#environment {
  background: var(--dp-white);
  border: 1px solid var(--dp-line);
}

#environment td {
  padding: 8px 12px;
  border: 1px solid var(--dp-line);
  color: var(--dp-ink);
}

#environment tr:nth-child(odd) {
  background-color: var(--dp-blue-soft);
}

.summary {
  background: var(--dp-white);
  border: 1px solid var(--dp-line);
  border-radius: 8px;
  padding: 8px 20px 16px;
  margin-top: 20px;
  margin-bottom: 20px;
}

.digipay-banner {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
  margin: 4px 0 12px;
  color: var(--dp-muted);
  font-size: 13px;
}

.digipay-chip {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  background: var(--dp-blue-soft);
  color: var(--dp-blue);
  font-weight: 600;
  font-size: 12px;
}

span.passed,
.passed .col-result {
  color: var(--dp-pass);
  font-weight: 600;
}

span.failed,
span.error,
.failed .col-result,
.error .col-result {
  color: var(--dp-fail);
  font-weight: 600;
}

#results-table {
  background: var(--dp-white);
  border: 1px solid var(--dp-line);
}

#results-table-head {
  background: var(--dp-blue);
  color: var(--dp-white);
}

.log,
.logwrapper {
  font-family: "IBM Plex Mono", Consolas, monospace;
  font-size: 12px;
}

html body > footer {
  display: block;
  margin-top: 32px;
  background: var(--dp-blue);
  color: #d6d6ff;
  padding: 18px 40px 28px;
  font-size: 12px;
  letter-spacing: 0.02em;
}

html body > footer::before {
  content: "Digipay · Software QA Engineer · Checkout API task (EN)";
  display: block;
  color: var(--dp-white);
  font-weight: 600;
  margin-bottom: 6px;
}

html body > footer::after {
  content: "Local suite · Playwright APIRequestContext · pytest-html";
  display: block;
}

#data-container {
  display: none;
}
"""

out = Path(__file__).with_name("report.css")
out.write_text(css.replace("__LOGO__", b64), encoding="utf-8")
print(f"wrote {out}")
