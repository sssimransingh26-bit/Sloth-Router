const $ = (sel) => document.querySelector(sel);
const demos = [];

async function boot() {
  const status = await fetch("/api/status").then((r) => r.json());
  const badge = $("#mode-badge");
  badge.textContent = status.mode;
  badge.className = `badge ${status.mode}`;
  const examples = await fetch("/api/examples").then((r) => r.json());
  demos.splice(0, demos.length, ...examples);
  renderMetrics(status);
}

function renderMetrics(status) {
  const host = $("#metrics-body");
  const rows = status.results && status.results.systems;
  if (!rows || !rows.length) {
    host.className = "empty-card";
    host.innerHTML =
      'Benchmark not run yet. After training, <code>python -m eval.run --systems A,B,C,D --split test</code> fills this table from <code>results/table.json</code>.';
    drawCurve([]);
    return;
  }
  host.className = "";
  const fmt = (x) => (typeof x === "number" ? x.toFixed(3) : "—");
  host.innerHTML = `<table>
    <thead><tr><th>System</th><th>Route acc.</th><th>Dangerous error</th><th>Answer correct</th><th>Cost / 1k</th><th>Latency</th></tr></thead>
    <tbody>${rows
      .map(
        (r) => `<tr>
        <td>${r.system}</td>
        <td>${fmt(r.route_acc)}</td>
        <td>${fmt(r.dangerous_error)}</td>
        <td>${fmt(r.answer_correct)}</td>
        <td>$${fmt(r.cost_per_1k_usd)}</td>
        <td>${fmt(r.latency_ms_mean)} ms</td>
      </tr>`
      )
      .join("")}</tbody></table>`;
  drawCurve(rows);
}

function drawCurve(rows) {
  const svg = $("#curve");
  svg.innerHTML = "";
  const w = 480;
  const h = 220;
  const pad = 36;
  const ns = "http://www.w3.org/2000/svg";
  const add = (name, attrs) => {
    const el = document.createElementNS(ns, name);
    Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
    svg.appendChild(el);
    return el;
  };
  add("line", { x1: pad, y1: h - pad, x2: w - 16, y2: h - pad, stroke: "#c9d4c8" });
  add("line", { x1: pad, y1: 16, x2: pad, y2: h - pad, stroke: "#c9d4c8" });
  if (!rows.length) {
    add("text", { x: 80, y: 110, fill: "#5c6b60", "font-size": "14" }).textContent =
      "Curve appears after eval writes results/table.json";
    return;
  }
  const xs = rows.map((r) => r.cost_per_1k_usd || 0);
  const ys = rows.map((r) => r.answer_correct || 0);
  const xmax = Math.max(0.01, ...xs);
  const x = (v) => pad + (v / xmax) * (w - pad - 24);
  const y = (v) => h - pad - v * (h - pad - 24);
  rows.forEach((r) => {
    add("circle", {
      cx: x(r.cost_per_1k_usd || 0),
      cy: y(r.answer_correct || 0),
      r: 6,
      fill: "#3f5a45",
    });
    add("text", {
      x: x(r.cost_per_1k_usd || 0) + 8,
      y: y(r.answer_correct || 0) - 8,
      fill: "#243028",
      "font-size": "11",
    }).textContent = r.system;
  });
}

function light(route) {
  document.querySelectorAll(".lane").forEach((el) => {
    el.classList.toggle("on", el.dataset.lane === route);
  });
}

async function ask(question) {
  $("#q").value = question;
  $("#think").hidden = false;
  light(null);
  $("#answer").textContent = "thinking slowly…";
  const res = await fetch("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  const data = await res.json();
  $("#think").hidden = true;
  if (data.error) {
    $("#answer").textContent = data.error;
    $("#why").textContent = data.detail || "error";
    return;
  }
  light(data.route);
  $("#answer").textContent = data.answer || "No answer body.";
  $("#cost").textContent = data.cost_usd != null ? `$${Number(data.cost_usd).toFixed(5)}` : "—";
  $("#lat").textContent = data.latency_ms != null ? `${data.latency_ms} ms` : "—";
  $("#why").textContent = data.reason || data.mode || "—";
  $("#conf").textContent = data.confidence != null ? Number(data.confidence).toFixed(2) : "—";
  if (data.badge) {
    const badge = $("#mode-badge");
    badge.textContent = data.badge;
    badge.className = `badge ${data.mode || data.badge}`;
  }
}

$("#ask-form").addEventListener("submit", (e) => {
  e.preventDefault();
  ask($("#q").value.trim());
});

document.querySelectorAll("[data-demo]").forEach((btn) => {
  btn.addEventListener("click", () => {
    const item = demos[Number(btn.dataset.demo)];
    if (item) ask(item.question);
    else location.hash = "#play";
  });
});

boot();
