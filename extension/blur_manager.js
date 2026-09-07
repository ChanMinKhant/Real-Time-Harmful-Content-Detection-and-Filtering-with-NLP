/**
 * Harmful Content Blur Guard - Blur & Interaction Manager
 * Handles element styling, hierarchy double-click reveal, and link/button locks.
 */

window.BlurManager = (function () {
  const userRevealedElements = new WeakSet();
  let lastClickTime = 0;
  let lastClickTarget = null;

  function isUserRevealed(el) {
    if (!el) return false;
    return userRevealedElements.has(el) ||
           el.dataset?.nlpRevealed === "true" ||
           el.classList?.contains("nlp-blur-revealed") ||
           Boolean(el.closest && el.closest('[data-nlp-revealed="true"], .nlp-blur-revealed'));
  }

  function applyBlur(el, res, settings) {
    if (!settings.enabled || !res || !res.is_harmful) return;
    if (res.score < settings.threshold) return;
    if (isUserRevealed(el)) return;

    // Category filter check
    const cat = (res.category || "").toLowerCase();
    if (cat.includes("hate") && !settings.filterHateSpeech) return;
    if (cat.includes("bullying") && !settings.filterCyberbullying) return;
    if (cat.includes("profanity") && !settings.filterProfanity) return;
    if (cat.includes("toxic") && !settings.filterToxicity) return;

    el.classList.remove("nlp-blur-revealed");
    el.classList.add("nlp-blur-active");
    el.setAttribute("data-nlp-blurred", "true");
    el.dataset.nlpNeedsBlur = "true";
    delete el.dataset.nlpRevealed;
    const categoryLabel = (res.category || "Harmful Content").toUpperCase();
    const confidencePct = Math.round((res.score || 0) * 100);
    el.setAttribute("title", `⚠️ [${categoryLabel} (${confidencePct}%)] Blurred. Double-click to unblur.`);
  }

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

    // 2. All ancestors with blur class or attribute
    let curr = target;
    while (curr && curr !== document.body && curr !== document.documentElement) {
      if (curr.classList && (curr.classList.contains('nlp-blur-active') || curr.hasAttribute('data-nlp-blurred'))) {
        nodesToUnblur.add(curr);
      }
      curr = curr.parentElement;
    }

    // 3. Parent container and all descendant children
    const container = (target.closest && target.closest('.Message, .message, .comment-item, .comment, .post-card, .post, .bubble-content, .text-content, div[role="article"]')) || target.parentElement;
    if (container) {
      if (container.classList && (container.classList.contains('nlp-blur-active') || container.hasAttribute('data-nlp-blurred'))) {
        nodesToUnblur.add(container);
      }
      const children = container.querySelectorAll ? container.querySelectorAll('.nlp-blur-active, [data-nlp-blurred="true"]') : [];
      children.forEach(c => nodesToUnblur.add(c));
    }

    // 4. Force permanent unblur on all gathered nodes
    nodesToUnblur.forEach(node => {
      node.classList.remove('nlp-blur-active');
      node.classList.add('nlp-blur-revealed');
      node.removeAttribute('data-nlp-blurred');
      delete node.dataset.nlpNeedsBlur;
      node.dataset.nlpRevealed = "true";
      userRevealedElements.add(node);
      node.removeAttribute('title');
    });

    console.log(`👁️ [Harmful Content Guard] Permanently unblurred ${nodesToUnblur.size} node(s).`);
  }

  function handleTwoClickTiming(target, e) {
    if (!target || !target.closest) return false;
    const blurred = target.closest('.nlp-blur-active, [data-nlp-blurred="true"]');
    if (!blurred) return false;

    const now = Date.now();
    const isSame = (lastClickTarget === blurred);
    const diff = now - lastClickTime;

    lastClickTime = now;
    lastClickTarget = blurred;

    // Detect 2 rapid clicks within 450ms
    if (isSame && diff > 30 && diff < 450) {
      lastClickTime = 0;
      lastClickTarget = null;
      unblurElement(blurred, e);
      return true;
    }
    return false;
  }

  function initInteractionListeners() {
    // Capture phase pointerdown & mousedown for rapid double-click detection
    window.addEventListener('mousedown', (e) => handleTwoClickTiming(e.target, e), true);
    window.addEventListener('pointerdown', (e) => handleTwoClickTiming(e.target, e), true);

    // Native dblclick
    window.addEventListener('dblclick', (e) => {
      if (!e.target || !e.target.closest) return;
      const blurred = e.target.closest('.nlp-blur-active, [data-nlp-blurred="true"]');
      if (blurred) unblurElement(blurred, e);
    }, true);

    // Prevent navigation / interaction on single click of blurred element
    window.addEventListener('click', (e) => {
      if (!e.target || !e.target.closest) return;
      const blurred = e.target.closest('.nlp-blur-active, [data-nlp-blurred="true"]');
      if (blurred) {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
      }
    }, true);

    // Prevent middle-click open on blurred elements
    window.addEventListener('auxclick', (e) => {
      if (!e.target || !e.target.closest) return;
      const blurred = e.target.closest('.nlp-blur-active, [data-nlp-blurred="true"]');
      if (blurred) {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
      }
    }, true);
  }

  function clearAllBlurs() {
    document.querySelectorAll(".nlp-blur-active, .nlp-blur-revealed, [data-nlp-blurred]").forEach(el => {
      el.classList.remove("nlp-blur-active", "nlp-blur-revealed");
      el.removeAttribute("data-nlp-blurred");
      delete el.dataset.nlpNeedsBlur;
      delete el.dataset.nlpRevealed;
      el.removeAttribute("title");
    });
  }

  return {
    isUserRevealed,
    applyBlur,
    unblurElement,
    initInteractionListeners,
    clearAllBlurs
  };
})();
