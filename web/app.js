const statusEl = document.querySelector("#status");
const warningsEl = document.querySelector("#warnings");
const nodesEl = document.querySelector("#nodes");
const basesEl = document.querySelector("#bases");
const debugEl = document.querySelector("#debug");
const warmthBar = document.querySelector("#warmthBar");
const targetName = document.querySelector("#targetName");
const roundInfo = document.querySelector("#roundInfo");
const nodeCount = document.querySelector("#nodeCount");
const baseCount = document.querySelector("#baseCount");
const showTarget = document.querySelector("#showTarget");
const audioMode = document.querySelector("#audioMode");
const timer = document.querySelector("#timer");

let audio;
let latestWarmth = 0;

function ensureAudio() {
  if (audio) return audio;
  const ctx = new AudioContext();
  const gain = ctx.createGain();
  gain.gain.value = 0.04;
  gain.connect(ctx.destination);
  audio = { ctx, gain, lastClick: 0, drone: null };
  return audio;
}

function setAudioWarmth(value) {
  latestWarmth = Math.max(0, Math.min(1, value || 0));
  if (!audio) return;
  const now = audio.ctx.currentTime;
  if (audioMode.value === "drone") {
    if (!audio.drone) {
      const osc = audio.ctx.createOscillator();
      osc.type = "sine";
      osc.connect(audio.gain);
      osc.start();
      audio.drone = osc;
    }
    audio.drone.frequency.value = 80 + latestWarmth * 420;
    audio.gain.gain.value = 0.015 + latestWarmth * 0.045;
    return;
  }
  if (audio.drone) {
    audio.drone.stop();
    audio.drone = null;
  }
  const interval = 0.85 - latestWarmth * 0.72;
  if (now - audio.lastClick > interval) {
    const osc = audio.ctx.createOscillator();
    const clickGain = audio.ctx.createGain();
    osc.frequency.value = 260 + latestWarmth * 900;
    clickGain.gain.setValueAtTime(0.08, now);
    clickGain.gain.exponentialRampToValueAtTime(0.001, now + 0.045);
    osc.connect(clickGain);
    clickGain.connect(audio.ctx.destination);
    osc.start(now);
    osc.stop(now + 0.05);
    audio.lastClick = now;
  }
}

async function api(method, path, body = undefined) {
  ensureAudio();
  const response = await fetch(path, {
    method,
    headers: { "content-type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await response.json();
  if (!response.ok && data.error) throw new Error(data.error);
  render(data);
  return data;
}

function render(data) {
  statusEl.textContent = data.source_ok ? `${data.source} online` : "RuView offline";
  statusEl.style.color = data.source_ok ? "#86efac" : "#fca5a5";
  const warnings = data.warnings || [];
  warningsEl.hidden = warnings.length === 0;
  warningsEl.innerHTML = warnings.map((warning) => `<div>${escapeHtml(warning)}</div>`).join("");

  const values = data.values || {};
  const maxValue = Math.max(1, ...Object.values(values).map(Number));
  nodesEl.innerHTML = Object.keys(values).sort((a, b) => Number(a) - Number(b)).map((nodeId) => {
    const value = Number(values[nodeId]);
    const pct = Math.min(100, (value / maxValue) * 100);
    return `<div class="node"><strong>Node ${nodeId}</strong><div>${value.toFixed(2)}</div><div class="meter"><div style="width:${pct}%"></div></div></div>`;
  }).join("");
  nodeCount.textContent = `${(data.node_ids || []).length} nodes`;

  const bases = data.bases || [];
  baseCount.textContent = `${bases.length} bases`;
  basesEl.innerHTML = bases.map((base) => {
    const bars = Object.entries(base.signature || {}).sort((a, b) => Number(a[0]) - Number(b[0])).map(([nodeId, value]) => {
      const pct = Math.min(100, Number(value) * 12);
      return `<div>n${nodeId}<div class="meter"><div style="width:${pct}%"></div></div></div>`;
    }).join("");
    return `<div class="base"><header><strong>${escapeHtml(base.name)}</strong><button class="secondary" onclick="deleteBase('${base.id}')">x</button></header>${bars}</div>`;
  }).join("");

  const warmth = Number(data.warmth || 0);
  warmthBar.style.width = `${Math.round(warmth * 100)}%`;
  setAudioWarmth(warmth);

  if (data.target?.hidden) {
    targetName.textContent = "Hidden";
  } else if (data.target?.name) {
    targetName.textContent = data.target.name;
  } else {
    targetName.textContent = "None";
  }
  const state = data.state || {};
  roundInfo.textContent = `Mode ${state.mode || "idle"}, round ${state.round || 0}, score ${state.score || 0}`;

  showTarget.checked = Boolean(data.settings?.show_target ?? true);
  audioMode.value = data.settings?.audio_mode || audioMode.value;
  timer.value = data.settings?.timer_seconds || "";
  debugEl.textContent = JSON.stringify(data, null, 2);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  }[char]));
}

async function refresh() {
  try {
    const response = await fetch("/api/snapshot");
    render(await response.json());
  } catch (error) {
    statusEl.textContent = "Geist offline";
    statusEl.style.color = "#fca5a5";
  }
}

async function withBusy(button, work) {
  button.disabled = true;
  try {
    await work();
  } catch (error) {
    alert(error.message);
  } finally {
    button.disabled = false;
  }
}

document.querySelector("#baselineBtn").addEventListener("click", (event) => {
  withBusy(event.currentTarget, () => api("POST", "/api/layout/baseline", { seconds: 10 }));
});

document.querySelector("#resetBtn").addEventListener("click", (event) => {
  if (confirm("Reset layout and bases?")) withBusy(event.currentTarget, () => api("POST", "/api/layout/reset", {}));
});

document.querySelector("#baseBtn").addEventListener("click", (event) => {
  const current = Number.parseInt(baseCount.textContent, 10) || 0;
  const name = document.querySelector("#baseName").value || `Base ${current + 1}`;
  withBusy(event.currentTarget, () => api("POST", "/api/bases/capture", { name, seconds: 12 }));
});

document.querySelector("#startBtn").addEventListener("click", (event) => {
  withBusy(event.currentTarget, () => api("POST", "/api/game/start", {
    show_target: showTarget.checked,
    timer_seconds: timer.value ? Number(timer.value) : null,
  }));
});

document.querySelector("#nextBtn").addEventListener("click", (event) => {
  withBusy(event.currentTarget, () => api("POST", "/api/game/next", {}));
});

document.querySelector("#stopBtn").addEventListener("click", (event) => {
  withBusy(event.currentTarget, () => api("POST", "/api/game/stop", {}));
});

showTarget.addEventListener("change", () => api("PATCH", "/api/game/settings", { show_target: showTarget.checked }));
audioMode.addEventListener("change", () => api("PATCH", "/api/game/settings", { audio_mode: audioMode.value }));
timer.addEventListener("change", () => api("PATCH", "/api/game/settings", { timer_seconds: timer.value ? Number(timer.value) : null }));

window.deleteBase = (id) => api("DELETE", `/api/bases/${id}`);

setInterval(refresh, 250);
refresh();
