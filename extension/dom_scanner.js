/**
 * Harmful Content Blur Guard - DOM Scanner & In-Browser Tier 1 Matcher
 * Uses TreeWalker traversal and MutationObserver with requestIdleCallback debouncing.
 */

window.BlurDomScanner = (function () {
  const SKIP_TAGS = new Set([
    'script', 'style', 'noscript', 'svg', 'code', 'pre',
    'input', 'textarea', 'select', 'iframe', 'canvas',
    'video', 'audio', 'img'
  ]);

  const INLINE_TAGS = new Set([
    'a', 'b', 'i', 'em', 'strong', 'u', 's', 'span', 'small', 'mark',
    'br', 'sub', 'sup'
  ]);

  // Myanmar syllable segmentation regex (covers stacked subscript + kinzi \u103A?\u1039[cons])
  const MM_SYLLABLE_RE = /(?<![\u103A\u1039])([\u1000-\u1021\u1023-\u102A\u103F\u104E](?:[\u103A]?[\u1039][\u1000-\u1021])*(?:[\u103B-\u103E])*(?:[\u102B-\u1035\u1031\u1032])*(?:[\u1000-\u1021\u1023-\u102A\u103F]\u103A(?!\u1039))?(?:\u103A(?!\u1039))*[\u1036\u1037\u1038]*)/g;

  function escapeRe(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function mmSyllableJoin(text) {
    const syls = text.match(MM_SYLLABLE_RE);
    return syls ? syls.join(' ') : text;
  }

  const OBF_SIGNAL_RE = /[0-9@#$+|<!*]/;

  // Compile Tier 1 patterns from BLUR_RULES
  let compiledEnPatterns = null;
  let compiledMmPatterns = null;

  function initPatterns() {
    if (!window.BLUR_RULES) return;
    const rules = window.BLUR_RULES;
    const leetMap = (rules.leetspeak && rules.leetspeak.char_map) || {};
    const obfExtra = (rules.leetspeak && rules.leetspeak.obfuscation_patterns) || {};

    function tolerantChar(ch) {
      if (!/[a-z]/i.test(ch)) return escapeRe(ch);
      const low = ch.toLowerCase();
      return '[' + low + (obfExtra[low] || '') + ']+';
    }

    // English patterns
    compiledEnPatterns = {};
    for (const [cat, words] of Object.entries(rules.english_lexicon || {})) {
      const unique = [...new Set(words)];
      const plain = unique.map(w => `\\b${escapeRe(w)}\\b`).sort((a, b) => b.length - a.length).join('|');
      const tolerant = unique.map(w => w.split('').map(c => c === ' ' ? '\\s+' : tolerantChar(c)).join('')).join('|');
      compiledEnPatterns[cat] = {
        plain: new RegExp(plain, 'i'),
        tolerant: new RegExp(`\\b(?:${tolerant})\\b`, 'i')
      };
    }

    // Myanmar patterns
    compiledMmPatterns = {};
    for (const [cat, words] of Object.entries(rules.myanmar_lexicon || {})) {
      const tokens = [];
      for (const word of new Set(words)) {
        const syls = word.match(MM_SYLLABLE_RE);
        if (!syls || syls.length === 0) continue;
        const joined = syls.map(escapeRe).join('\\s+');
        tokens.push(`(?<!\\S)${joined}(?!\\S)`);
      }
      if (tokens.length > 0) {
        tokens.sort((a, b) => b.length - a.length);
        compiledMmPatterns[cat] = new RegExp(tokens.join('|'));
      }
    }
  }

  function deobfuscate(text) {
    if (!window.BLUR_RULES) return text;
    const leetMap = (window.BLUR_RULES.leetspeak && window.BLUR_RULES.leetspeak.char_map) || {};
    if (!/[0-9!$5+|<]/.test(text)) return text;
    return text.replace(/(?<=[A-Za-z])[0-9!$|<+]/g, (ch) => leetMap[ch] || ch);
  }

  function checkLocalLexicon(text) {
    if (!text) return null;
    if (!compiledEnPatterns || !compiledMmPatterns) initPatterns();
    if (!compiledEnPatterns || !compiledMmPatterns) return null;

    const cleaned = deobfuscate(text.toLowerCase());

    // 1. English Matcher
    for (const [cat, patterns] of Object.entries(compiledEnPatterns)) {
      let match = cleaned.match(patterns.plain);
      if (!match && OBF_SIGNAL_RE.test(cleaned)) {
        match = cleaned.match(patterns.tolerant);
      }
      if (match) {
        const score = (cat === 'profanity' || cat === 'hate_speech') ? 0.96 : 0.88;
        return {
          is_harmful: true,
          score: score,
          category: cat,
          keyword: match[0],
          tier_used: "Tier 1 (Instant Local Filter)",
          reason: `Detected harmful keyword '${match[0]}' [${cat.toUpperCase()}]`
        };
      }
    }

    // 2. Myanmar Matcher
    const joined = mmSyllableJoin(text);
    for (const [cat, regex] of Object.entries(compiledMmPatterns)) {
      const match = joined.match(regex);
      if (match) {
        const keyword = match[0].replace(/\s+/g, '');
        const score = (cat === 'profanity' || cat === 'hate_speech') ? 0.96 : 0.88;
        return {
          is_harmful: true,
          score: score,
          category: cat,
          keyword: keyword,
          tier_used: "Tier 1 (Instant Local Filter)",
          reason: `Detected harmful keyword '${keyword}' [${cat.toUpperCase()}]`
        };
      }
    }

    return null;
  }

  function isCandidateElement(node) {
    if (!node || node.nodeType !== Node.ELEMENT_NODE) return false;
    const tag = node.tagName.toLowerCase();

    if (SKIP_TAGS.has(tag)) return false;
    if (node.isContentEditable) return false;

    if (node.classList.contains('nlp-blur-active') || node.classList.contains('nlp-blur-revealed') || node.dataset.nlpRevealed === "true") {
      return false;
    }

    // Leaf preference: skip parents whose non-inline children already contain the content
    for (const child of node.children) {
      if (INLINE_TAGS.has(child.tagName.toLowerCase())) continue;
      const childText = (child.textContent || "").trim();
      if (childText.length >= 2) return false;
    }

    const text = (node.textContent || "").trim();
    if (!text || text.length < 2 || text.length > 1500) return false;

    return true;
  }

  function collectCandidates(rootNode) {
    const candidates = new Set();
    const walker = document.createTreeWalker(rootNode, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const parent = node.parentElement;
        if (!parent) return NodeFilter.FILTER_REJECT;
        const tag = parent.tagName.toLowerCase();
        if (SKIP_TAGS.has(tag) || parent.isContentEditable) return NodeFilter.FILTER_REJECT;
        const t = node.nodeValue ? node.nodeValue.trim() : "";
        if (t.length < 2) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });

    let tn;
    while ((tn = walker.nextNode())) {
      candidates.add(tn.parentElement);
    }
    return candidates;
  }

  return {
    initPatterns,
    checkLocalLexicon,
    isCandidateElement,
    collectCandidates
  };
})();
