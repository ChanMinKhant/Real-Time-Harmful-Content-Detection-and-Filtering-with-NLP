/**
 * Popup Script for Harmful Content Blurry Guard Extension
 */

const API_CANDIDATES = [
  "http://127.0.0.1:5001/api",
  "http://127.0.0.1:5000/api",
  "http://localhost:5001/api",
  "http://localhost:5000/api"
];
let API_BASE = API_CANDIDATES[0];

// Elements
const mainToggle = document.getElementById("main-toggle");
const sensitivitySlider = document.getElementById("sensitivity-slider");
const thresholdVal = document.getElementById("threshold-val");
const statusIndicator = document.getElementById("status-indicator");
const statusText = document.getElementById("status-text");

const catHate = document.getElementById("cat-hate");
const catBullying = document.getElementById("cat-bullying");
const catProfanity = document.getElementById("cat-profanity");
const catToxicity = document.getElementById("cat-toxicity");

const statBlurred = document.getElementById("stat-blurred");
const statScanned = document.getElementById("stat-scanned");
const statLatency = document.getElementById("stat-latency");

const testInput = document.getElementById("test-input");
const testBtn = document.getElementById("test-btn");
const testResult = document.getElementById("test-result");

// Load stored preferences
function initPopup() {
  if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
    chrome.storage.local.get(["nlp_settings", "nlp_stats"], (res) => {
      const s = res.nlp_settings || {};
      if (s.enabled !== undefined) mainToggle.checked = s.enabled;
      if (s.threshold !== undefined) {
        sensitivitySlider.value = Math.round(s.threshold * 100);
        thresholdVal.innerText = `${sensitivitySlider.value}%`;
      }
      if (s.filterHateSpeech !== undefined) catHate.checked = s.filterHateSpeech;
      if (s.filterCyberbullying !== undefined) catBullying.checked = s.filterCyberbullying;
      if (s.filterProfanity !== undefined) catProfanity.checked = s.filterProfanity;
      if (s.filterToxicity !== undefined) catToxicity.checked = s.filterToxicity;
      if (s.customBaseUrl) API_BASE = s.customBaseUrl;

      // Stats
      const st = res.nlp_stats || { scanned: 0, blurred: 0 };
      statBlurred.innerText = st.blurred || 0;
      statScanned.innerText = st.scanned || 0;
    });
  }

  checkBackendHealth();
}

// Save settings to Chrome storage
function saveSettings() {
  const newSettings = {
    enabled: mainToggle.checked,
    threshold: parseFloat(sensitivitySlider.value) / 100.0,
    filterHateSpeech: catHate.checked,
    filterCyberbullying: catBullying.checked,
    filterProfanity: catProfanity.checked,
    filterToxicity: catToxicity.checked,
    customBaseUrl: API_BASE
  };

  if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
    chrome.storage.local.set({ nlp_settings: newSettings });
  }
}

// Check Backend Health & Stats
async function checkBackendHealth() {
  const candidates = API_BASE ? [API_BASE, ...API_CANDIDATES.filter(u => u !== API_BASE)] : API_CANDIDATES;
  for (const candidate of candidates) {
    try {
      const clean = candidate.replace(/\/+$/, "");
      const res = await fetch(`${clean}/health`, { method: "GET" });
      if (res.ok) {
        API_BASE = clean;
        const data = await res.json();
        statusIndicator.className = "status-indicator online";
        statusText.innerText = "Online 🟢";

        if (data.pipeline_stats && data.pipeline_stats.avg_latency_ms !== undefined) {
          const avg = data.pipeline_stats.avg_latency_ms;
          statLatency.innerText = avg > 0 ? `~${avg}ms` : "~2ms";
        }
        return;
      }
    } catch (err) {
      // try next candidate
    }
  }
  statusIndicator.className = "status-indicator offline";
  statusText.innerText = "Offline 🔴";
  statLatency.innerText = "Offline";
}

// Event Listeners
mainToggle.addEventListener("change", saveSettings);

sensitivitySlider.addEventListener("input", () => {
  thresholdVal.innerText = `${sensitivitySlider.value}%`;
  saveSettings();
});

[catHate, catBullying, catProfanity, catToxicity].forEach(cb => {
  cb.addEventListener("change", saveSettings);
});

// Instant In-Popup NLP Tester
testBtn.addEventListener("click", async () => {
  const query = testInput.value.trim();
  if (!query) return;

  testBtn.disabled = true;
  testBtn.innerText = "...";
  testResult.style.display = "block";
  testResult.className = "test-result";
  testResult.innerHTML = "<em>Analyzing text...</em>";

  try {
    const threshold = parseFloat(sensitivitySlider.value) / 100.0;
    const payload = { text: query, threshold: threshold };

    if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.sendMessage) {
      chrome.runtime.sendMessage({ type: "ANALYZE_SINGLE", payload: payload }, (response) => {
        testBtn.disabled = false;
        testBtn.innerText = "Test";

        if (!response || !response.success || !response.data) {
          testResult.className = "test-result harmful";
          testResult.innerHTML = "<strong>Backend offline</strong>. Please ensure Flask server is running.";
          return;
        }

        renderTestResult(response.data);
      });
    } else {
      const res = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      testBtn.disabled = false;
      testBtn.innerText = "Test";
      renderTestResult(data);
    }
  } catch (err) {
    testBtn.disabled = false;
    testBtn.innerText = "Test";
    testResult.className = "test-result harmful";
    testResult.innerHTML = "<strong>Backend offline</strong>. Please run <code>python app.py</code>";
  }
});

function renderTestResult(data) {
  const confidence = Math.round(data.score * 100);
  const latency = data.latency_ms !== undefined ? `${data.latency_ms}ms` : "<1ms";
  if (data.is_harmful) {
    testResult.className = "test-result harmful";
    testResult.innerHTML = `
      <strong>⚠️ HARMFUL DETECTED (${confidence}%)</strong><br>
      <strong>Category:</strong> ${data.category}<br>
      <strong>Tier:</strong> ${data.tier_used} (${latency})<br>
      <small>${data.reason}</small>
    `;
  } else {
    testResult.className = "test-result safe";
    testResult.innerHTML = `
      <strong>✅ SAFE CONTENT</strong><br>
      <strong>Tier:</strong> ${data.tier_used} (${latency})<br>
      <small>${data.reason}</small>
    `;
  }
}

testInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    testBtn.click();
  }
});

// Initialize on open
document.addEventListener("DOMContentLoaded", initPopup);
