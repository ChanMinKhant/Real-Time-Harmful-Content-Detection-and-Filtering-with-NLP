/**
 * Harmful Content Blur Guard - Resilient API Client
 * Manages communication with the Chrome Background Service Worker proxy
 * and direct HTTP fallbacks across configured ports.
 */

window.BlurApiClient = (function () {
  const CANDIDATE_ENDPOINTS = [
    "http://127.0.0.1:5001/api",
    "http://127.0.0.1:5000/api",
    "http://localhost:5001/api",
    "http://localhost:5000/api"
  ];
  let activeBase = CANDIDATE_ENDPOINTS[0];

  function isExtensionValid() {
    try {
      return Boolean(typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.id);
    } catch (e) {
      return false;
    }
  }

  async function analyzeBatch(items, threshold, customBaseUrl) {
    const payload = { items, threshold };

    // 1. Try background service worker proxy first
    if (isExtensionValid()) {
      try {
        const bgRes = await new Promise((resolve, reject) => {
          chrome.runtime.sendMessage(
            { type: "ANALYZE_BATCH", payload },
            (response) => {
              if (chrome.runtime.lastError || !response || !response.success) {
                reject(chrome.runtime.lastError || new Error("Proxy error"));
              } else {
                resolve(response.data);
              }
            }
          );
        });
        if (bgRes) return bgRes;
      } catch (e) {
        // Fall through to direct fetch
      }
    }

    // 2. Direct HTTP Fallback across candidate endpoints
    const targets = customBaseUrl ? [customBaseUrl, ...CANDIDATE_ENDPOINTS] : [activeBase, ...CANDIDATE_ENDPOINTS.filter(u => u !== activeBase)];
    for (const base of targets) {
      try {
        const cleanBase = base.replace(/\/+$/, "");
        const url = `${cleanBase}/analyze-batch`;
        const res = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          activeBase = cleanBase;
          return await res.json();
        }
      } catch (err) {
        // Try next candidate
      }
    }

    return null;
  }

  async function analyzeSingle(text, threshold, customBaseUrl) {
    const payload = { text, threshold };

    if (isExtensionValid()) {
      try {
        const bgRes = await new Promise((resolve, reject) => {
          chrome.runtime.sendMessage(
            { type: "ANALYZE_SINGLE", payload },
            (response) => {
              if (chrome.runtime.lastError || !response || !response.success) {
                reject(chrome.runtime.lastError || new Error("Proxy error"));
              } else {
                resolve(response.data);
              }
            }
          );
        });
        if (bgRes) return bgRes;
      } catch (e) {
        // Fall through to direct fetch
      }
    }

    const targets = customBaseUrl ? [customBaseUrl, ...CANDIDATE_ENDPOINTS] : [activeBase, ...CANDIDATE_ENDPOINTS.filter(u => u !== activeBase)];
    for (const base of targets) {
      try {
        const cleanBase = base.replace(/\/+$/, "");
        const url = `${cleanBase}/analyze`;
        const res = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          activeBase = cleanBase;
          return await res.json();
        }
      } catch (err) {
        // Try next
      }
    }

    return null;
  }

  return {
    isExtensionValid,
    analyzeBatch,
    analyzeSingle,
    getActiveBase: () => activeBase,
    setActiveBase: (url) => { if (url) activeBase = url.replace(/\/+$/, ""); }
  };
})();
