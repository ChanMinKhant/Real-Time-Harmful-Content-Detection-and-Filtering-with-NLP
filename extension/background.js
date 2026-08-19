/**
 * Harmful Content Blurry Guard - Background Service Worker
 * Proxies API requests from Content Scripts to bypass HTTPS Mixed-Content & CSP restrictions on live websites (e.g. Telegram, Twitter, YouTube).
 */

const API_CANDIDATES = [
  "http://127.0.0.1:5001/api",
  "http://127.0.0.1:5000/api"
];
let activeApiBase = API_CANDIDATES[0];

async function checkOrFindActiveEndpoint() {
  for (const candidate of API_CANDIDATES) {
    try {
      const res = await fetch(`${candidate}/health`, { method: "GET" });
      if (res.ok) {
        activeApiBase = candidate;
        return candidate;
      }
    } catch (e) {
      // try next candidate
    }
  }
  return activeApiBase;
}

// Initial probe
checkOrFindActiveEndpoint();

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "ANALYZE_BATCH") {
    handleAnalyzeBatch(message.payload)
      .then(res => sendResponse({ success: true, data: res }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true; // Keep message channel open for async response
  }

  if (message.type === "ANALYZE_SINGLE") {
    handleAnalyzeSingle(message.payload)
      .then(res => sendResponse({ success: true, data: res }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (message.type === "GET_HEALTH") {
    checkOrFindActiveEndpoint()
      .then(endpoint => fetch(`${endpoint}/health`))
      .then(res => res.json())
      .then(data => sendResponse({ success: true, data: data }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }
});

async function handleAnalyzeBatch(payload) {
  const endpoint = await checkOrFindActiveEndpoint();
  const res = await fetch(`${endpoint}/analyze-batch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    throw new Error(`Backend returned status ${res.status}`);
  }
  return await res.json();
}

async function handleAnalyzeSingle(payload) {
  const endpoint = await checkOrFindActiveEndpoint();
  const res = await fetch(`${endpoint}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    throw new Error(`Backend returned status ${res.status}`);
  }
  return await res.json();
}
