const OUT = "reports/performance-report";

function esc(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/"/g, "&quot;");
}

function fmtValue(metric, key, value) {
  if (value == null) {
    return "-";
  }
  if (typeof value !== "number") {
    return String(value);
  }
  if (metric.contains === "time") {
    return `${value.toFixed(2)} ms`;
  }
  if (metric.contains === "data") {
    if (value >= 1024) {
      return `${(value / 1024).toFixed(1)} kB`;
    }
    return `${Math.round(value)} B`;
  }
  if (key === "rate" || metric.type === "rate") {
    return `${(value * 100).toFixed(2)}%`;
  }
  if (Number.isInteger(value)) {
    return String(value);
  }
  return value.toFixed(2);
}

function thresholdsOk(metrics) {
  return Object.values(metrics).every((metric) => {
    if (!metric.thresholds) {
      return true;
    }
    return Object.values(metric.thresholds).every((item) => item.ok);
  });
}

function pad(text, width) {
  const value = String(text);
  return value.length >= width ? value : value + " ".repeat(width - value.length);
}

function textSummary(data) {
  const metrics = data.metrics || {};
  const durationMs = (data.state && data.state.testRunDurationMs) || 0;
  const lines = [
    "",
    "  █ THRESHOLDS",
    "",
  ];

  let anyThreshold = false;
  for (const [name, metric] of Object.entries(metrics)) {
    if (!metric.thresholds) {
      continue;
    }
    anyThreshold = true;
    for (const [expr, result] of Object.entries(metric.thresholds)) {
      const mark = result.ok ? "✓" : "✗";
      lines.push(`    ${mark} ${name} '${expr}'`);
    }
  }
  if (!anyThreshold) {
    lines.push("    (none)");
  }

  lines.push("", "  █ TOTAL RESULTS", "");

  const checks = (data.root_group && data.root_group.checks) || [];
  if (checks.length) {
    for (const item of checks) {
      const mark = item.fails ? "✗" : "✓";
      lines.push(`    ${mark} ${item.name}  ${item.passes} passed / ${item.fails} failed`);
    }
    lines.push("");
  }

  const names = Object.keys(metrics).sort();
  for (const name of names) {
    const metric = metrics[name];
    const values = metric.values || {};
    const parts = Object.keys(values)
      .map((key) => `${key}=${fmtValue(metric, key, values[key])}`)
      .join("  ");
    lines.push(`    ${pad(name, 28)} ${parts}`);
  }

  lines.push("");
  lines.push(`    test duration: ${(durationMs / 1000).toFixed(1)}s`);
  lines.push("");
  return lines.join("\n");
}

function barChart(title, items, unit) {
  const max = Math.max(...items.map((item) => item.value), 0.0001);
  const bars = items
    .map((item) => {
      const width = Math.max(4, Math.round((item.value / max) * 220));
      const label = unit === "ms" ? `${item.value.toFixed(1)} ms` : `${(item.value * 100).toFixed(1)}%`;
      return `<div class="bar-row">
        <span>${esc(item.label)}</span>
        <svg width="240" height="16" aria-hidden="true">
          <rect x="0" y="3" width="240" height="10" rx="4" fill="#edf0f3"/>
          <rect x="0" y="3" width="${width}" height="10" rx="4" fill="#0000FF"/>
        </svg>
        <em>${esc(label)}</em>
      </div>`;
    })
    .join("");
  return `<div class="chart"><h3>${esc(title)}</h3>${bars}</div>`;
}

function donut(title, passRate) {
  const r = 36;
  const c = 2 * Math.PI * r;
  const safe = Math.min(1, Math.max(0, passRate));
  const dash = `${(safe * c).toFixed(2)} ${(c).toFixed(2)}`;
  const pct = `${(safe * 100).toFixed(1)}%`;
  return `<div class="chart donut">
    <h3>${esc(title)}</h3>
    <svg width="110" height="110" viewBox="0 0 110 110">
      <circle cx="55" cy="55" r="${r}" fill="none" stroke="#edf0f3" stroke-width="12"/>
      <circle cx="55" cy="55" r="${r}" fill="none" stroke="#0000FF" stroke-width="12"
        stroke-dasharray="${dash}" stroke-linecap="round" transform="rotate(-90 55 55)"/>
      <text x="55" y="60" text-anchor="middle" font-size="16" fill="#1d2433">${esc(pct)}</text>
    </svg>
  </div>`;
}

function durationItems(metric) {
  if (!metric || !metric.values) {
    return [];
  }
  const keys = ["min", "avg", "med", "p(90)", "p(95)", "max"];
  return keys
    .filter((key) => metric.values[key] != null)
    .map((key) => ({ label: key, value: metric.values[key] }));
}

function thresholdRows(metrics) {
  const rows = [];
  for (const [name, metric] of Object.entries(metrics)) {
    if (!metric.thresholds) {
      continue;
    }
    for (const [expr, result] of Object.entries(metric.thresholds)) {
      const cls = result.ok ? "ok" : "fail";
      rows.push(
        `<tr><td>${esc(name)}</td><td>${esc(expr)}</td><td class="${cls}">${
          result.ok ? "pass" : "fail"
        }</td></tr>`
      );
    }
  }
  return rows.length ? rows.join("") : "<tr><td colspan='3'>none</td></tr>";
}

function checkRows(data) {
  const checks = (data.root_group && data.root_group.checks) || [];
  if (!checks.length) {
    return "<tr><td colspan='4'>none</td></tr>";
  }
  return checks
    .map((item) => {
      const total = item.passes + item.fails;
      const cls = item.fails ? "fail" : "ok";
      return `<tr>
        <td>${esc(item.name)}</td>
        <td>${item.passes}</td>
        <td>${item.fails}</td>
        <td class="${cls}">${total ? ((item.passes / total) * 100).toFixed(2) : 0}%</td>
      </tr>`;
    })
    .join("");
}

function metricRows(metrics) {
  return Object.entries(metrics)
    .map(([name, metric]) => {
      const values = metric.values || {};
      const cells = Object.entries(values)
        .map(
          ([key, value]) =>
            `<span class="kv"><b>${esc(key)}</b> ${esc(fmtValue(metric, key, value))}</span>`
        )
        .join(" ");
      return `<tr><td>${esc(name)}</td><td>${esc(metric.type || "")}</td><td>${cells}</td></tr>`;
    })
    .join("");
}

function css() {
  return `
    @import url("https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap");
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
    html, body { height: 100%; background: var(--dp-paper); }
    body {
      font-family: "IBM Plex Sans", "Segoe UI", Helvetica, Arial, sans-serif;
      font-size: 14px; color: var(--dp-ink); margin: 0;
      min-height: 100vh; display: flex; flex-direction: column;
    }
    header { background: var(--dp-blue); color: var(--dp-white); padding: 24px 40px 0; }
    h1#title {
      display: flex; align-items: center; flex-wrap: wrap; gap: 16px;
      margin: 0; font-size: 26px; font-weight: 700;
    }
    h1#title::before {
      content: ""; width: 48px; height: 48px; flex: 0 0 48px; border-radius: 12px;
      background: var(--dp-white) url("../assets/MyDigiPay.png") center / 48px 48px no-repeat;
      box-shadow: 0 0 0 2px var(--dp-white);
    }
    h1#title::after {
      content: "Performance Testing · CHECKOUT";
      margin-left: auto; font-size: 11px; font-weight: 600; letter-spacing: 0.14em; opacity: 0.9;
    }
    .tagline {
      margin: 4px 0 0; padding: 0 0 22px; color: #d6d6ff;
      border-bottom: 3px solid var(--dp-white); font-size: 13px;
    }
    .subhead { padding: 14px 40px; background: var(--dp-blue-soft); font-size: 13px; }
    .subhead a { color: var(--dp-blue); font-weight: 600; }
    main { padding: 24px 40px 40px; max-width: 1100px; flex: 1 0 auto; }
    .badge { display: inline-block; padding: 4px 10px; border-radius: 999px; font-size: 13px; font-weight: 600; }
    .ok { color: var(--dp-pass); } .fail { color: var(--dp-fail); }
    .badge.ok { background: #d1e7dd; color: var(--dp-pass); }
    .badge.fail { background: #f8d7da; color: var(--dp-fail); }
    section {
      background: var(--dp-white); border: 1px solid var(--dp-line);
      border-radius: 10px; padding: 16px 18px; margin: 16px 0;
    }
    h2 {
      margin: 0 0 12px; font-size: 15px; font-weight: 600; color: var(--dp-blue);
      letter-spacing: 0.04em; text-transform: uppercase;
    }
    h3 { margin: 0 0 10px; font-size: 13px; color: var(--dp-muted); font-weight: 600; }
    .charts { display: flex; flex-wrap: wrap; gap: 16px; }
    .chart { flex: 1 1 280px; }
    .bar-row { display: grid; grid-template-columns: 52px 240px 1fr; gap: 8px;
      align-items: center; font-size: 13px; margin: 6px 0; }
    .bar-row em { font-style: normal; color: var(--dp-muted); }
    .donut { text-align: center; max-width: 180px; }
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--dp-line); vertical-align: top; }
    th { color: var(--dp-muted); font-weight: 600; }
    tr:nth-child(odd) td { background: var(--dp-blue-soft); }
    .kv { display: inline-block; margin: 0 12px 4px 0; white-space: nowrap; }
    .kv b { color: var(--dp-muted); margin-right: 4px; }
    pre {
      background: #1b1b2f; color: #d6d6ff; padding: 16px; border-radius: 8px;
      overflow: auto; font-size: 12px; line-height: 1.45;
      font-family: "IBM Plex Mono", Consolas, monospace;
    }
    footer {
      background: var(--dp-blue); color: #d6d6ff; padding: 12px 40px;
      font-size: 12px; letter-spacing: 0.02em; margin-top: auto; flex-shrink: 0;
    }
    footer strong { display: block; color: var(--dp-white); font-weight: 600; margin-bottom: 6px; }
  `;
}

function toHtml(name, data, terminal) {
  const metrics = data.metrics || {};
  const passed = thresholdsOk(metrics);
  const durationMs = (data.state && data.state.testRunDurationMs) || 0;
  const when = new Date().toISOString();
  const duration = metrics.http_req_duration;
  const failed = metrics.http_req_failed;
  const checks = metrics.checks;
  const failRate = failed && failed.values ? failed.values.rate || 0 : 0;
  const checkRate = checks && checks.values ? checks.values.rate || 0 : 0;
  const durationBars = durationItems(duration);
  const charts = [
    durationBars.length ? barChart("HTTP duration", durationBars, "ms") : "",
    donut("Checks passed", checkRate),
    barChart("HTTP result", [
      { label: "ok", value: 1 - failRate },
      { label: "failed", value: failRate },
    ], "%"),
  ].join("");

  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Digipay · Checkout Payment API - k6 Performance Test Report · ${esc(name)}</title>
  <style>${css()}</style>
</head>
<body>
  <header>
    <h1 id="title">Digipay · Checkout Payment API - k6 Performance Test Report</h1>
    <p class="tagline">HTML, charts, terminal dump, and JSON</p>
  </header>
  <div class="subhead">
    <a href="index.html">all reports</a> · <a href="${esc(name)}.json">full JSON</a>
    · k6 ${esc(name)} · ${esc(when)} · ${(durationMs / 1000).toFixed(1)}s
    · <span class="badge ${passed ? "ok" : "fail"}">${passed ? "thresholds passed" : "thresholds failed"}</span>
  </div>
  <main>
    <section>
      <h2>Charts</h2>
      <div class="charts">${charts}</div>
    </section>
    <section>
      <h2>Terminal output</h2>
      <pre>${esc(terminal)}</pre>
    </section>
    <section>
      <h2>Thresholds</h2>
      <table>
        <tr><th>metric</th><th>rule</th><th>result</th></tr>
        ${thresholdRows(metrics)}
      </table>
    </section>
    <section>
      <h2>Checks</h2>
      <table>
        <tr><th>name</th><th>pass</th><th>fail</th><th>rate</th></tr>
        ${checkRows(data)}
      </table>
    </section>
    <section>
      <h2>All metrics</h2>
      <table>
        <tr><th>name</th><th>type</th><th>values</th></tr>
        ${metricRows(metrics)}
      </table>
    </section>
  </main>
  <footer>
    <strong>Digipay · Software QA Engineer · Checkout API task (EN)</strong>
    Local suite · k6 ${esc(name)} · GET /payment/ · Mockoon
  </footer>
</body>
</html>
`;
}

function indexHtml() {
  const items = ["smoke", "load", "spike", "stress"];
  const links = items 
    .map((name) => `<li><a href="${name}.html">${name}</a> · <a href="${name}.json">json</a></li>`)
    .join("");
  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Digipay · Checkout Payment API - k6 Performance Test Report · k6</title>
  <style>${css()}</style>
</head>
<body>
  <header>
    <h1 id="title">Digipay · Checkout Payment API - k6 Performance Test Report</h1>
    <p class="tagline">HTML, charts, terminal dump, and JSON</p>
  </header>
  <main>
    <section>
      <ul>${links}</ul>
    </section>
  </main>
  <footer>
    <strong>Digipay · Software QA Engineer · Checkout API task (EN)</strong>
    Local suite · k6 · GET /payment/ · Mockoon
  </footer>
</body>
</html>
`;
}

export function handleHtmlSummary(name) {
  return function (data) {
    const terminal = textSummary(data);
    return {
      stdout: terminal,
      [`${OUT}/${name}.html`]: toHtml(name, data, terminal),
      [`${OUT}/${name}.json`]: JSON.stringify(data, null, 2),
      [`${OUT}/index.html`]: indexHtml(),
    };
  };
}
