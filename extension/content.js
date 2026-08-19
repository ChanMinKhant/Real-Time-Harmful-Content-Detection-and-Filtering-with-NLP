/**
 * Real-time Harmful Content Blur Guard (Content Script)
 * Architecture:
 * - Tier 1 (Client-Side Fast Lexicon Filter): 0ms Instant detection for explicit toxic keywords (EN & MM)
 * - Tier 2 (Backend NLP Pipeline): Asynchronous deep contextual ML classification for ambiguous text
 * - Complete Hierarchy Unblur (unblurs all nested blurred ancestors & children on double-click)
 * - Link / Button lock protection while blurred
 * - Extension Context Invalidation Safe
 */

(function () {
  console.log("🛡️ [Harmful Content Guard] Engine active on:", window.location.href);

  // ---------------------------------------------------------------------------
  // 1. Curated Bilingual Lexicons for Instant 0ms In-Extension Filtering
  // ---------------------------------------------------------------------------
  const MM_LEXICON = {
    hate_speech: [
      "ကုလား", "ကုလားဆိုး", "တရုတ်ခွေး", "ခွေးကုလား", "ဘာသာဖျက်",
      "မိစ္ဆာဒိဌိ", "ခွေးမျိုး", "ကုလားဖြူ", "ကုလားမဲ", "လူမျိုးတုံး",
      "မျိုးမစစ်", "တိုင်းတစ်ပါးသားခွေး", "ကုလားဂျင်း"
    ],
    cyberbullying: [
      "သေလိုက်ပါလား", "သွားသေလိုက်", "မင်းအသက်ရှင်နေတာအပိုပဲ", "ရုပ်ကိုကဆိုးတာ",
      "မျက်နှာမွဲ", "အရုပ်ဆိုး", "အဆီပုတ်", "ဖက်တီး", "ဝက်လိုကောင်", "ဝက်မ",
      "နုံချာလိုက်တာ", "ငတုံး", "မအ", "မအေဘေး", "လဒ", "ငကြောင်", "အသုံးမကျတဲ့ကောင်",
      "အသုံးမကျတဲ့ဟာ", "မျက်နှာပြောင်", "မရှက်ဘူးလား", "ရွံစရာကောင်းလိုက်တာ"
    ],
    profanity: [
      "လိုး", "လိုးမ", "လိုးမသား", "မအေလိုး", "မအေလိုးသား", "ဖာသည်", "ဖာသယ်",
      "ဖာခေါင်း", "ဖာသည်မ", "ခွေးမသား", "ခွေးသူတောင်းစား", "လီး", "လီးပဲ", "လီးလား",
      "စောက်ရမ်း", "စောက်ပတ်", "စောက်ဖုတ်", "စောက်ရူး", "စောက်ကျိုးနည်း",
      "စောက်သုံးမကျ", "စောက်ချိုး", "စောက်ပေါ", "ခွေးလိုကောင်", "ခွေးမ", "ခွေးသား"
    ],
    insult: [
      "လူယုတ်မာ", "သူတောင်းစား", "သူခိုး", "လိမ်ညာတဲ့ကောင်", "ငနပိ",
      "တောသား", "အရူး", "ရူးနေလား", "အပေါစား", "အောက်တန်းစား", "အဆင့်မရှိတဲ့ကောင်",
      "လိမ်ဖုတ်", "ကောက်ကျစ်တဲ့ကောင်", "ကလေကချေ"
    ]
  };

  const EN_LEXICON = {
    hate_speech: [
      "nigger", "nigga", "faggot", "kike", "chink", "wetback", "retard",
      "white trash", "islamophobic", "terrorist", "subhuman", "filthy immigrant"
    ],
    cyberbullying: [
      "kill yourself", "kys", "die already", "go die", "nobody likes you",
      "ugly freak", "worthless piece of shit", "waste of oxygen", "fat ugly pig",
      "loser", "you are pathetic", "disgusting pig", "jump off a cliff"
    ],
    profanity: [
      "fuck", "fucking", "fucked", "motherfucker", "bitch", "bitches",
      "cunt", "asshole", "bastard", "dick", "pussy", "shit", "bullshit",
      "cock", "slut", "whore", "dumbass", "dipshit", "jackass"
    ],
    insult: [
      "idiot", "moron", "stupid", "imbecile", "trash", "scumbag",
      "clown", "garbage", "pathetic loser", "brainless", "incompetent"
    ]
  };

  function compilePatterns(lexicon) {
    const map = {};
    for (const [cat, words] of Object.entries(lexicon)) {
      const escaped = words.map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).sort((a, b) => b.length - a.length);
      map[cat] = new RegExp(`(${escaped.join('|')})`, 'i');
    }
    return map;
  }

  const MM_PATTERNS = compilePatterns(MM_LEXICON);
  const EN_PATTERNS = compilePatterns(EN_LEXICON);

  function checkLocalLexicon(text) {
    if (!text) return null;
    const lower = text.toLowerCase();

    // Check English
    for (const [cat, regex] of Object.entries(EN_PATTERNS)) {
      const match = lower.match(regex);
      if (match) {
        return {
          is_harmful: true,
          score: (cat === 'profanity' || cat === 'hate_speech') ? 0.96 : 0.88,
          category: cat,
          keyword: match[0],
          tier_used: "Tier 1 (Instant Local Filter)",
          reason: `Detected harmful keyword '${match[0]}' [${cat.toUpperCase()}]`
        };
      }
    }

    // Check Myanmar
    for (const [cat, regex] of Object.entries(MM_PATTERNS)) {
      const match = text.match(regex);
      if (match) {
        return {
          is_harmful: true,
          score: (cat === 'profanity' || cat === 'hate_speech') ? 0.96 : 0.88,
          category: cat,
          keyword: match[0],
          tier_used: "Tier 1 (Instant Local Filter)",
          reason: `Detected harmful keyword '${match[0]}' [${cat.toUpperCase()}]`
        };
      }
    }

    return null;
  }

  // ---------------------------------------------------------------------------
  // 2. State & Extension Validity Guard
  // ---------------------------------------------------------------------------
  function isExtensionValid() {
    try {
      return Boolean(typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.id);
    } catch (e) {
      return false;
    }
  }

  let settings = {
    enabled: true,
    threshold: 0.6,
    filterToxicity: true,
    filterCyberbullying: true,
    filterHateSpeech: true,
    filterProfanity: true
  };

  const processedNodes = new WeakSet();
  const userRevealedElements = new WeakSet();
  const textHashMap = new Map(); // Hash -> Result
  let pendingBatch = [];
  let debounceTimer = null;
  let elementIdCounter = 0;
  const elementsRegistry = new Map();

  const BACKEND_CANDIDATES = [
    "http://127.0.0.1:5001/api/analyze-batch",
    "http://127.0.0.1:5000/api/analyze-batch"
  ];
  let activeBackendUrl = BACKEND_CANDIDATES[0];

  // Broad selectors for leaf & near-leaf text elements
  const BROAD_SELECTORS = [
    'p', 'span', 'a', 'button', 'li', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    // Telegram Web (K & A versions)
    '.translatable-message', '.text-content', '.message-text', '.content-inner',
    // Twitter / X
    '[data-testid="tweetText"]',
    // YouTube
    '#content-text', 'yt-formatted-string.ytd-comment-renderer',
    // Reddit
    '[data-testid="post-comment"]', 'div[slot="comment"]',
    // Generic
    '[data-comment]', '.comment-text', '.post-content', '.tweet-text'
  ].join(', ');

  function hashString(str) {
    let hash = 5381;
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5) + hash) + str.charCodeAt(i);
      hash |= 0;
    }
    return hash.toString();
  }

  function loadSettings() {
    if (!isExtensionValid()) return;
    try {
      chrome.storage.local.get(["nlp_settings"], (res) => {
        if (chrome.runtime.lastError) return;
        if (res && res.nlp_settings) {
          settings = { ...settings, ...res.nlp_settings };
        }
      });
    } catch (e) {}
  }

  if (isExtensionValid() && chrome.storage && chrome.storage.onChanged) {
    try {
      chrome.storage.onChanged.addListener((changes, area) => {
        if (!isExtensionValid()) return;
        if (area === "local" && changes.nlp_settings) {
          settings = { ...settings, ...changes.nlp_settings.newValue };
          if (!settings.enabled) {
            document.querySelectorAll(".nlp-blur-active, .nlp-blur-revealed").forEach(el => {
              el.classList.remove("nlp-blur-active", "nlp-blur-revealed");
              delete el.dataset.nlpRevealed;
              el.removeAttribute("title");
            });
          } else {
            scanDOM(document.body);
          }
        }
      });
    } catch (e) {}
  }

  // ---------------------------------------------------------------------------
  // 3. Complete Hierarchy Double-Click Reveal (One-Way Permanent Unblur)
  // ---------------------------------------------------------------------------
  let lastClickTime = 0;
  let lastClickTarget = null;

  function unblurElement(target, e) {
    if (!target) return;
    if (e) {
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();
    }

    const nodesToUnblur = new Set();

    // 1. Target node
    if (target.nodeType === Node.ELEMENT_NODE) {
      nodesToUnblur.add(target);
    }

    // 2. All ancestors with blur class
    let curr = target;
    while (curr && curr !== document.body && curr !== document.documentElement) {
      if (curr.classList && curr.classList.contains('nlp-blur-active')) {
        nodesToUnblur.add(curr);
      }
      curr = curr.parentElement;
    }

    // 3. Parent container and all descendant children
    const container = (target.closest && (target.closest('.Message, .message, .comment-item, .comment, .post-card, .post, .bubble-content, .text-content, div[role="article"]') || target.parentElement)) || target.parentElement;
    if (container) {
      if (container.classList && container.classList.contains('nlp-blur-active')) {
        nodesToUnblur.add(container);
      }
      const children = container.querySelectorAll ? container.querySelectorAll('.nlp-blur-active') : [];
      children.forEach(c => nodesToUnblur.add(c));
    }

    // 4. Force unblur on all gathered nodes
    nodesToUnblur.forEach(node => {
      node.classList.remove('nlp-blur-active');
      node.classList.add('nlp-blur-revealed');
      node.dataset.nlpRevealed = "true";
      userRevealedElements.add(node);
      node.removeAttribute('title');
    });

    console.log(`👁️ [Harmful Content Guard] Permanently unblurred ${nodesToUnblur.size} node(s) for target:`, target);
  }

  function handleTwoClickTiming(target, e) {
    if (!target || !target.closest) return false;
    const blurred = target.closest('.nlp-blur-active');
    if (!blurred) return false;

    const now = Date.now();
    const isSame = (lastClickTarget === blurred);
    const diff = now - lastClickTime;

    lastClickTime = now;
    lastClickTarget = blurred;

    // Detected 2 clicks within 450ms
    if (isSame && diff > 30 && diff < 450) {
      lastClickTime = 0;
      lastClickTarget = null;
      unblurElement(blurred, e);
      return true;
    }
    return false;
  }

  // Capture phase mousedown & pointerdown
  window.addEventListener('mousedown', (e) => {
    handleTwoClickTiming(e.target, e);
  }, true);

  window.addEventListener('pointerdown', (e) => {
    handleTwoClickTiming(e.target, e);
  }, true);

  // Native dblclick event
  window.addEventListener('dblclick', (e) => {
    if (!e.target || !e.target.closest) return;
    const blurred = e.target.closest('.nlp-blur-active');
    if (blurred) {
      unblurElement(blurred, e);
    }
  }, true);

  // Prevent single-click navigation/actions on blurred elements
  window.addEventListener('click', (e) => {
    if (!e.target || !e.target.closest) return;
    const blurred = e.target.closest('.nlp-blur-active');
    if (blurred) {
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();
    }
  }, true);

  // Prevent middle-click open on blurred elements
  window.addEventListener('auxclick', (e) => {
    if (!e.target || !e.target.closest) return;
    const blurred = e.target.closest('.nlp-blur-active');
    if (blurred) {
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();
    }
  }, true);

  // ---------------------------------------------------------------------------
  // 4. Candidate Filter & DOM Scanner
  // ---------------------------------------------------------------------------
  function isCandidateElement(node) {
    if (!node || node.nodeType !== Node.ELEMENT_NODE) return false;
    const tag = node.tagName.toLowerCase();

    const ignoredTags = [
      'script', 'style', 'noscript', 'svg', 'code', 'pre',
      'input', 'textarea', 'select', 'iframe', 'canvas',
      'video', 'audio', 'img'
    ];
    if (ignoredTags.includes(tag)) return false;
    if (node.isContentEditable) return false;

    // Skip elements already blurred or revealed by user
    if (userRevealedElements.has(node) || node.dataset.nlpRevealed === "true" || node.classList.contains('nlp-blur-active') || node.classList.contains('nlp-blur-revealed')) {
      return false;
    }

    // Leaf preference: if a child has text, evaluate the child instead of the parent container
    let hasTextChild = false;
    for (let i = 0; i < node.children.length; i++) {
      const child = node.children[i];
      const childText = (child.innerText || child.textContent || "").trim();
      if (childText.length >= 2 && !ignoredTags.includes(child.tagName.toLowerCase())) {
        hasTextChild = true;
        break;
      }
    }
    if (hasTextChild && tag !== 'a' && tag !== 'button') {
      return false;
    }

    const text = (node.innerText || node.textContent || "").trim();
    if (!text || text.length < 2 || text.length > 1500) return false;

    return true;
  }

  function scanDOM(rootNode) {
    if (!settings.enabled || !rootNode) return;

    if (isCandidateElement(rootNode) && !processedNodes.has(rootNode)) {
      evaluateElement(rootNode);
    }

    const elements = rootNode.querySelectorAll ? rootNode.querySelectorAll(BROAD_SELECTORS) : [];
    for (let i = 0; i < elements.length; i++) {
      const el = elements[i];
      if (userRevealedElements.has(el) || el.dataset.nlpRevealed === "true" || el.classList.contains('nlp-blur-revealed')) continue;
      if (processedNodes.has(el)) continue;
      if (!isCandidateElement(el)) continue;
      evaluateElement(el);
    }

    if (pendingBatch.length > 0) {
      scheduleBatchDispatch();
    }
  }

  // Evaluate element: Tier 1 Instant Local Lexicon -> Tier 2 Backend NLP
  function evaluateElement(el) {
    const text = (el.innerText || el.textContent || "").trim();
    if (text.length < 2 || text.length > 1500) return;

    processedNodes.add(el);

    const hash = hashString(text);

    // 1. Check memory cache
    if (textHashMap.has(hash)) {
      applyResult(el, textHashMap.get(hash));
      return;
    }

    // 2. Tier 1: Instant Local Lexicon Filter (0ms latency!)
    const localResult = checkLocalLexicon(text);
    if (localResult) {
      localResult.text = text;
      textHashMap.set(hash, localResult);
      applyResult(el, localResult);
      return;
    }

    // 3. Tier 2: Queue for Backend NLP Pipeline
    const nodeId = `nlp_el_${++elementIdCounter}`;
    elementsRegistry.set(nodeId, el);
    pendingBatch.push({ id: nodeId, text: text, hash: hash });
  }

  function scheduleBatchDispatch() {
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      dispatchBatch();
    }, 150);
  }

  // ---------------------------------------------------------------------------
  // 5. Batch Dispatcher (Background Service Worker Proxy + Direct Fallback)
  // ---------------------------------------------------------------------------
  function dispatchBatch() {
    if (pendingBatch.length === 0) return;

    const currentBatch = pendingBatch.splice(0, 40);
    const payloadItems = currentBatch.map(item => ({ id: item.id, text: item.text }));

    if (isExtensionValid()) {
      try {
        chrome.runtime.sendMessage(
          {
            type: "ANALYZE_BATCH",
            payload: {
              items: payloadItems,
              threshold: settings.threshold
            }
          },
          (response) => {
            if (!isExtensionValid() || chrome.runtime.lastError || !response || !response.success) {
              fallbackDirectFetch(currentBatch, payloadItems);
              return;
            }
            processBatchResults(currentBatch, response.data);
          }
        );
      } catch (err) {
        fallbackDirectFetch(currentBatch, payloadItems);
      }
    } else {
      fallbackDirectFetch(currentBatch, payloadItems);
    }
  }

  async function fallbackDirectFetch(currentBatch, payloadItems) {
    const urlsToTry = [activeBackendUrl, ...BACKEND_CANDIDATES.filter(u => u !== activeBackendUrl)];
    for (const url of urlsToTry) {
      try {
        const res = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            items: payloadItems,
            threshold: settings.threshold
          })
        });
        if (res.ok) {
          activeBackendUrl = url;
          const data = await res.json();
          processBatchResults(currentBatch, data);
          return;
        }
      } catch (e) {}
    }
  }

  function processBatchResults(batch, data) {
    if (!data) return;
    const results = data.results || [];

    results.forEach(res => {
      const el = elementsRegistry.get(res.id);
      if (el) {
        const match = batch.find(b => b.id === res.id);
        if (match) {
          textHashMap.set(match.hash, res);
        }
        applyResult(el, res);
        elementsRegistry.delete(res.id);
      }
    });

    updateStats(results);
  }

  // ---------------------------------------------------------------------------
  // 6. Apply Blur to Element
  // ---------------------------------------------------------------------------
  function applyResult(el, res) {
    if (!settings.enabled || !res || !res.is_harmful) return;
    if (res.score < settings.threshold) return;

    // Do NOT re-blur if user has revealed this element
    if (userRevealedElements.has(el) || el.dataset.nlpRevealed === "true" || el.classList.contains("nlp-blur-revealed")) {
      return;
    }

    // Check category filter settings
    const cat = (res.category || "").toLowerCase();
    if (cat.includes("hate") && !settings.filterHateSpeech) return;
    if (cat.includes("bullying") && !settings.filterCyberbullying) return;
    if (cat.includes("profanity") && !settings.filterProfanity) return;
    if (cat.includes("toxic") && !settings.filterToxicity) return;

    el.classList.remove("nlp-blur-revealed");
    el.classList.add("nlp-blur-active");
    const categoryLabel = (res.category || "Harmful Content").toUpperCase();
    el.setAttribute("title", `⚠️ [${categoryLabel}] Blurred & Locked. Double-click to unblur.`);

    console.log(`🛡️ [Harmful Content Guard] Blurred (${res.tier_used || 'Tier 1'}): "${(res.text || '').substring(0, 30)}..." [${res.category}] (Score: ${res.score})`);
  }

  function updateStats(results) {
    if (!isExtensionValid() || !chrome.storage || !chrome.storage.local) return;
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

  // ---------------------------------------------------------------------------
  // 7. Observer & Periodic Poller
  // ---------------------------------------------------------------------------
  function initObserver() {
    const observer = new MutationObserver((mutations) => {
      for (let i = 0; i < mutations.length; i++) {
        const mutation = mutations[i];
        if (mutation.addedNodes && mutation.addedNodes.length > 0) {
          for (let j = 0; j < mutation.addedNodes.length; j++) {
            const node = mutation.addedNodes[j];
            if (node.nodeType === Node.ELEMENT_NODE) {
              scanDOM(node);
            }
          }
        } else if (mutation.type === 'characterData' && mutation.target.parentElement) {
          scanDOM(mutation.target.parentElement);
        }
      }
    });

    observer.observe(document.body || document.documentElement, {
      childList: true,
      subtree: true,
      characterData: true
    });

    setInterval(() => {
      if (document.visibilityState === "visible") {
        scanDOM(document.body);
      }
    }, 2500);
  }

  // Startup initialization
  loadSettings();
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
