/**
 * Real-time Harmful Content Blur Guard (Content Script Orchestrator)
 * Connects BlurRules, BlurApiClient, BlurManager, and BlurDomScanner.
 */

(function () {
  console.log("🛡️ [Harmful Content Guard] Engine v2.0 active on:", window.location.href);

  const ApiClient = window.BlurApiClient;
  const BlurManager = window.BlurManager;
  const DomScanner = window.BlurDomScanner;

  let settings = {
    enabled: true,
    threshold: 0.6,
    customBaseUrl: "",
    filterToxicity: true,
    filterCyberbullying: true,
    filterHateSpeech: true,
    filterProfanity: true
  };

  const processedNodes = new WeakSet();
  const textHashMap = new Map();
  let pendingBatch = [];
  let debounceTimer = null;
  let elementIdCounter = 0;
  const elementsRegistry = new Map();

  function hashString(str) {
    let hash = 5381;
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5) + hash) + str.charCodeAt(i);
      hash |= 0;
    }
    return hash.toString();
  }

  function loadSettings() {
    if (!ApiClient.isExtensionValid()) return;
    try {
      chrome.storage.local.get(["nlp_settings"], (res) => {
        if (chrome.runtime.lastError) return;
        if (res && res.nlp_settings) {
          settings = { ...settings, ...res.nlp_settings };
          if (settings.customBaseUrl) {
            ApiClient.setActiveBase(settings.customBaseUrl);
          }
        }
      });
    } catch (e) {}
  }

  if (ApiClient.isExtensionValid() && chrome.storage && chrome.storage.onChanged) {
    try {
      chrome.storage.onChanged.addListener((changes, area) => {
        if (!ApiClient.isExtensionValid()) return;
        if (area === "local" && changes.nlp_settings) {
          settings = { ...settings, ...changes.nlp_settings.newValue };
          if (settings.customBaseUrl) {
            ApiClient.setActiveBase(settings.customBaseUrl);
          }
          if (!settings.enabled) {
            BlurManager.clearAllBlurs();
          } else {
            scanDOM(document.body);
          }
        }
      });
    } catch (e) {}
  }

  function evaluateElement(el) {
    if (!el || BlurManager.isUserRevealed(el)) return;
    const text = DomScanner.extractCleanText ? DomScanner.extractCleanText(el) : (el.textContent || "").trim();
    if (text.length < 2 || text.length > 1500) return;

    processedNodes.add(el);
    const hash = hashString(text);

    // 1. Check in-memory cache
    if (textHashMap.has(hash)) {
      BlurManager.applyBlur(el, textHashMap.get(hash), settings);
      return;
    }

    // 2. Tier 1: Instant Local Lexicon Filter (0ms)
    const localResult = DomScanner.checkLocalLexicon(text);
    if (localResult) {
      localResult.text = text;
      textHashMap.set(hash, localResult);
      BlurManager.applyBlur(el, localResult, settings);
      return;
    }

    // 3. Tier 2 & 3: Queue for Backend NLP Pipeline
    const nodeId = `nlp_el_${++elementIdCounter}`;
    elementsRegistry.set(nodeId, el);
    pendingBatch.push({ id: nodeId, text: text, hash: hash });
  }

  function scheduleBatchDispatch() {
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      dispatchBatch();
    }, 120);
  }

  async function dispatchBatch() {
    if (pendingBatch.length === 0) return;

    const currentBatch = pendingBatch.splice(0, 50);
    const payloadItems = currentBatch.map(item => ({ id: item.id, text: item.text }));

    const data = await ApiClient.analyzeBatch(payloadItems, settings.threshold, settings.customBaseUrl);
    if (data && data.results) {
      data.results.forEach(res => {
        const el = elementsRegistry.get(res.id);
        if (el) {
          const match = currentBatch.find(b => b.id === res.id);
          if (match) {
            textHashMap.set(match.hash, res);
          }
          BlurManager.applyBlur(el, res, settings);
          elementsRegistry.delete(res.id);
        }
      });
      updateStats(data.results);
    }
  }

  function updateStats(results) {
    if (!ApiClient.isExtensionValid() || !chrome.storage || !chrome.storage.local) return;
    try {
      chrome.storage.local.get(["nlp_stats"], (res) => {
        if (chrome.runtime.lastError) return;
        let stats = (res && res.nlp_stats) || { scanned: 0, blurred: 0 };
        stats.scanned += results.length;
        stats.blurred += results.filter(r => r.is_harmful && r.score >= settings.threshold).length;
        chrome.storage.local.set({ nlp_stats: stats });
      });
    } catch (e) {}
  }

  function scanDOM(rootNode) {
    if (!settings.enabled || !rootNode) return;

    const candidates = DomScanner.collectCandidates(rootNode);
    candidates.forEach(el => {
      if (processedNodes.has(el)) return;
      if (!DomScanner.isCandidateElement(el)) return;
      evaluateElement(el);
    });

    if (pendingBatch.length > 0) {
      scheduleBatchDispatch();
    }
  }

  // Targeted MutationObserver with requestIdleCallback scheduling
  const pendingRoots = [];
  let scanQueued = false;

  function queueScan(rootNode) {
    if (!settings.enabled || !rootNode) return;
    for (let i = pendingRoots.length - 1; i >= 0; i--) {
      if (pendingRoots[i] === rootNode || pendingRoots[i].contains(rootNode)) return;
      if (rootNode.contains(pendingRoots[i])) pendingRoots.splice(i, 1);
    }
    pendingRoots.push(rootNode);

    if (!scanQueued) {
      scanQueued = true;
      const runner = (cb) => {
        if (window.requestIdleCallback) {
          window.requestIdleCallback(cb, { timeout: 200 });
        } else {
          setTimeout(cb, 100);
        }
      };
      runner(() => {
        scanQueued = false;
        const roots = pendingRoots.splice(0);
        for (const r of roots) scanDOM(r);
      });
    }
  }

  function initObserver() {
    const observer = new MutationObserver((mutations) => {
      for (let i = 0; i < mutations.length; i++) {
        const mutation = mutations[i];
        if (mutation.addedNodes && mutation.addedNodes.length > 0) {
          for (let j = 0; j < mutation.addedNodes.length; j++) {
            const node = mutation.addedNodes[j];
            if (node.nodeType === Node.ELEMENT_NODE) {
              queueScan(node);
            }
          }
        } else if (mutation.type === 'characterData' && mutation.target.parentElement) {
          queueScan(mutation.target.parentElement);
        } else if (mutation.type === 'attributes') {
          const target = mutation.target;
          if (target && target.nodeType === Node.ELEMENT_NODE) {
            // If React/Teact stripped our blur attribute/class on a harmful node that hasn't been unblurred, restore it
            if (target.dataset && target.dataset.nlpNeedsBlur === "true" && !BlurManager.isUserRevealed(target)) {
              if (!target.classList.contains('nlp-blur-active')) {
                target.classList.add('nlp-blur-active');
              }
              if (!target.hasAttribute('data-nlp-blurred')) {
                target.setAttribute('data-nlp-blurred', 'true');
              }
            }
          }
        }
      }
    });

    observer.observe(document.body || document.documentElement, {
      childList: true,
      subtree: true,
      characterData: true,
      attributes: true,
      attributeFilter: ['class', 'data-nlp-blurred']
    });
  }

  // Initialize
  loadSettings();
  BlurManager.initInteractionListeners();
  DomScanner.initPatterns();

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      scanDOM(document.body);
      initObserver();
    });
  } else {
    scanDOM(document.body);
    initObserver();
  }
})();
