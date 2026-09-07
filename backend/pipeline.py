"""
High-Performance Cascading NLP Classification Pipeline.
Architecture:
- Tier 0: In-Memory LRU Cache (< 0.1ms)
- Tier 1: Lexicon & Syllable/N-gram Pattern Matching (< 1ms)
- Tier 2: TF-IDF + Calibrated Linear ML Classifier (< 5ms)
- Tier 3: Contextual Ensemble (+ optional Transformer, 10 - 30ms)

Academic Highlights:
- Speed vs Accuracy Trade-off optimization
- Trained artifacts loaded from backend/models/ (train_model.py), with seed fallback
- Optional English transformer tier (lazy-loaded, gracefully skipped when unavailable)
- Detailed latency tracking per tier, thread-safe statistics & cache
"""

import hashlib
import json
import os
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sklearn.ensemble import VotingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB

from dataset import SEED_CORPUS
from lexicon_mm import CATEGORY_LABELS, fast_lexicon_check
from normalizer import preprocess_text

MODELS_DIR = Path(__file__).resolve().parent / "models"

HATE_HINTS = ["hate", "immigrant", "terrorist", "subhuman", "racist", "ကုလား", "လူမျိုး", "ဘာသာဖျက်", "မျိုးမစစ်"]
PROFANITY_HINTS = [
    "fuck", "bitch", "shit", "asshole", "cunt", "dick", "pussy", "bastard",
    "လိုး", "ခွေး", "စောက်", "လီး", "ဖာ", "ဖာသည်", "မအေလိုး"
]
INSULT_HINTS = ["idiot", "moron", "stupid", "imbecile", "trash", "clown", "ငတုံး", "အရူး", "အောက်တန်းစား", "လူယုတ်မာ"]

BENIGN_CONVERSATIONAL_PHRASES = {
    "you", "how are you", "how are you doing", "how are you today", "are you there",
    "are you okay", "are you free", "where are you", "who are you", "what about you",
    "can you help", "could you help", "thank you", "thanks", "hello", "hi", "hey",
    "good morning", "good evening", "good afternoon", "see you", "welcome", "take care",
    "take care of yourself", "ok", "okay", "yes", "no", "sure", "nice to meet you",
    "မင်း", "မင်း နေကောင်းလား", "နေကောင်းလား", "မင်္ဂလာပါ", "မင်္ဂလာမနက်ခင်းပါ",
    "ကျေးဇူးတင်ပါတယ်", "ဟုတ်ကဲ့", "ဟုတ်တယ်", "ဘာလုပ်နေလဲ", "မင်း ဘာလုပ်နေလဲ"
}

BENIGN_TOKENS = {
    "you", "your", "yours", "me", "my", "mine", "he", "him", "his", "she", "her", "hers",
    "we", "us", "our", "ours", "they", "them", "their", "theirs", "it", "its",
    "are", "is", "am", "was", "were", "be", "been", "being",
    "how", "what", "where", "when", "why", "who", "which", "there", "here",
    "to", "the", "a", "an", "and", "or", "in", "on", "at", "for", "with", "about",
    "hi", "hello", "hey", "yes", "no", "ok", "okay", "thanks", "thank",
    "မင်း", "သူ", "ငါ", "ကျွန်တော်", "ကျွန်မ", "တို့", "တွေ", "ပါ", "နော်", "ဗျာ", "ခင်ဗျာ",
    "နေကောင်းလား", "မင်္ဂလာပါ", "ကျေးဇူးတင်ပါတယ်", "ဟုတ်ကဲ့", "ဟုတ်တယ်"
}


def is_purely_benign_conversational(text: str, tokens: Optional[List[str]] = None) -> bool:
    cleaned = text.strip().lower().rstrip("?!.,;:")
    if cleaned in BENIGN_CONVERSATIONAL_PHRASES:
        return True
    toks = tokens or cleaned.split()
    if toks and all(t.lower().rstrip("?!.,;:") in BENIGN_TOKENS for t in toks if t.strip()):
        return True
    return False


class CascadingNLPPipeline:
    """Multi-tiered NLP engine for real-time bilingual toxicity detection."""

    def __init__(self, cache_size: int = 3000, enable_transformer: bool = True):
        # Tier 0: LRU Cache
        self.cache_size = cache_size
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._lock = threading.Lock()

        # Optional transformer state (lazy-loaded on first Tier 3 use)
        self.enable_transformer = enable_transformer
        self.transformer_pipeline = None
        self._transformer_checked = False
        self._transformer_lock = threading.Lock()

        # Performance Statistics
        self.stats = {
            "total_queries": 0,
            "tier0_cache_hits": 0,
            "tier1_lexicon_hits": 0,
            "tier2_ml_hits": 0,
            "tier3_transformer_hits": 0,
            "avg_latency_ms": 0.0,
            "total_latency_ms": 0.0,
        }

        self.model_metadata: Dict[str, Any] = {}
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tier2_model: Optional[LogisticRegression] = None
        self.tier3_ensemble: Optional[VotingClassifier] = None

        self._init_models()

    # ------------------------------------------------------------------
    # Model initialization: trained artifacts -> inline fallback
    # ------------------------------------------------------------------
    def _load_artifacts(self) -> bool:
        meta_file = MODELS_DIR / "metadata.json"
        if not meta_file.exists():
            return False
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            self.vectorizer = joblib_load("vectorizer.joblib")
            self.tier2_model = joblib_load("tier2_logreg.joblib")
            self.tier3_ensemble = joblib_load("tier3_ensemble.joblib")
            self.model_metadata = metadata
            print(f"📚 [NLP Pipeline] Loaded trained artifacts v{metadata.get('model_version')} "
                  f"(F1: t2={metadata.get('f1_harmful_tier2')}, t3={metadata.get('f1_harmful_tier3')}, "
                  f"n={metadata.get('dataset_size')})")
            return True
        except Exception as exc:
            print(f"⚠️ [NLP Pipeline] Artifact load notice ({exc.__class__.__name__}: {exc}); using seed fallback.")
            return False

    def _fit_inline_fallback(self):
        texts = [item[0] for item in SEED_CORPUS]
        labels = [item[1] for item in SEED_CORPUS]

        # Character & Word N-gram Vectorizer (captures Myanmar syllables and English subwords)
        self.vectorizer = TfidfVectorizer(
            analyzer='char_wb',
            ngram_range=(2, 5),
            min_df=1,
            sublinear_tf=True
        )
        X = self.vectorizer.fit_transform(texts)

        # Tier 2 Fast Model
        self.tier2_model = LogisticRegression(C=1.5, class_weight='balanced', max_iter=1000, random_state=42)
        self.tier2_model.fit(X, labels)

        # Tier 3 Calibrated Ensemble Model (Voting Classifier)
        clf1 = LogisticRegression(C=2.0, class_weight='balanced', max_iter=1000, random_state=42)
        clf2 = MultinomialNB(alpha=0.3)
        self.tier3_ensemble = VotingClassifier(
            estimators=[('lr', clf1), ('nb', clf2)],
            voting='soft'
        )
        self.tier3_ensemble.fit(X, labels)
        self.model_metadata = {"model_version": "inline-fallback"}
        print("🌱 [NLP Pipeline] Inline fallback model fitted successfully.")

    def _init_models(self):
        """Loads trained artifacts if present; otherwise fits the seed corpus."""
        if not self._load_artifacts():
            self._fit_inline_fallback()

    # ------------------------------------------------------------------
    # Optional Tier 3 transformer (lazy, graceful fallback)
    # ------------------------------------------------------------------
    def _get_transformer(self):
        if not self.enable_transformer or self._transformer_checked:
            return self.transformer_pipeline
        with self._transformer_lock:
            if self._transformer_checked:
                return self.transformer_pipeline
            self._transformer_checked = True
            if os.environ.get("NLP_TRANSFORMER", "auto").lower() in ("off", "false", "0"):
                return None
            try:
                from transformers import pipeline as hf_pipeline
                self.transformer_pipeline = hf_pipeline(
                    "text-classification",
                    model="unitary/toxic-bert",
                    top_k=None,
                    truncation=True,
                    max_length=256,
                )
                print("🤖 [NLP Pipeline] English transformer tier active (unitary/toxic-bert)")
            except Exception as exc:
                print(f"ℹ️ [NLP Pipeline] Transformer skipped ({exc.__class__.__name__}); using ensemble.")
        return self.transformer_pipeline

    def _transformer_toxicity(self, text: str, lang: str) -> Optional[float]:
        if lang == "my":
            return None  # toxic-bert is English-only; ensemble handles MM
        pipe = self._get_transformer()
        if pipe is None:
            return None
        try:
            scores = pipe(text[:512])[0]
            return float(max(s["score"] for s in scores))
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Cache and Stats Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _hash_text(text: str) -> str:
        return hashlib.md5(text.strip().encode('utf-8')).hexdigest()

    def _cache_get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            if cache_key in self.cache:
                self.cache.move_to_end(cache_key)
                return self.cache[cache_key].copy()
        return None

    def _save_cache(self, key: str, value: Dict[str, Any]):
        with self._lock:
            if len(self.cache) >= self.cache_size:
                self.cache.popitem(last=False)
            self.cache[key] = value

    def clear_cache(self):
        with self._lock:
            self.cache.clear()

    def _update_stats(self, latency_ms: float):
        with self._lock:
            self.stats["total_latency_ms"] += latency_ms
            if self.stats["total_queries"] > 0:
                self.stats["avg_latency_ms"] = round(
                    self.stats["total_latency_ms"] / self.stats["total_queries"], 2
                )

    def reset_stats(self):
        with self._lock:
            self.stats = {
                "total_queries": 0,
                "tier0_cache_hits": 0,
                "tier1_lexicon_hits": 0,
                "tier2_ml_hits": 0,
                "tier3_transformer_hits": 0,
                "avg_latency_ms": 0.0,
                "total_latency_ms": 0.0,
            }
            self.cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                **self.stats,
                "cache_items_count": len(self.cache),
                "model_metadata": self.model_metadata,
            }

    @staticmethod
    def _guess_category(cleaned_text: str) -> str:
        text_low = cleaned_text.lower()
        if any(w in text_low for w in HATE_HINTS):
            return "hate_speech"
        if any(w in text_low for w in PROFANITY_HINTS):
            return "profanity"
        if any(w in text_low for w in INSULT_HINTS):
            return "insult"
        return "cyberbullying"

    def _empty_result(self, raw_text: str) -> Dict[str, Any]:
        return {
            "text": raw_text,
            "is_harmful": False,
            "score": 0.0,
            "category": "safe",
            "language": "en",
            "tier_used": "Tier 0 (Empty)",
            "reason": "Empty text string",
            "latency_ms": 0.05,
        }

    # ------------------------------------------------------------------
    # Single prediction (cascading tiers)
    # ------------------------------------------------------------------
    def predict(self, raw_text: str, sensitivity_threshold: float = 0.6) -> Dict[str, Any]:
        start_time = time.perf_counter()
        with self._lock:
            self.stats["total_queries"] += 1

        text = raw_text.strip() if raw_text else ""
        if not text:
            return self._empty_result(text)

        # -------------------------------------------------------------
        # TIER 0: In-Memory LRU Cache (< 0.1ms)
        # -------------------------------------------------------------
        cache_key = f"{self._hash_text(text)}_{sensitivity_threshold}"
        cached_result = self._cache_get(cache_key)
        if cached_result is not None:
            with self._lock:
                self.stats["tier0_cache_hits"] += 1
            latency = (time.perf_counter() - start_time) * 1000.0
            cached_result["latency_ms"] = round(latency, 2)
            cached_result["tier_used"] = "Tier 0 (LRU Cache)"
            self._update_stats(latency)
            return cached_result

        # Text Preprocessing & Language Identification
        cleaned_text, lang, tokens = preprocess_text(text)

        # -------------------------------------------------------------
        # TIER 1: Fast Lexicon & Syllable Pattern Filter (< 1ms)
        # -------------------------------------------------------------
        lexicon_res = fast_lexicon_check(cleaned_text, lang)
        if lexicon_res and lexicon_res[1] >= sensitivity_threshold:
            _, score, category, matched_word, reason = lexicon_res
            with self._lock:
                self.stats["tier1_lexicon_hits"] += 1
            latency = (time.perf_counter() - start_time) * 1000.0
            result = {
                "text": raw_text,
                "is_harmful": True,
                "score": round(score, 3),
                "category": category,
                "language": lang,
                "tier_used": "Tier 1 (Lexicon/Pattern Filter)",
                "matched_keyword": matched_word,
                "reason": reason,
                "latency_ms": round(latency, 2),
            }
            self._save_cache(cache_key, result)
            self._update_stats(latency)
            return result

        # Guardrail: Polite conversational phrases and neutral pronouns
        if is_purely_benign_conversational(cleaned_text, tokens):
            with self._lock:
                self.stats["tier1_lexicon_hits"] += 1
            latency = (time.perf_counter() - start_time) * 1000.0
            result = {
                "text": raw_text,
                "is_harmful": False,
                "score": 0.05,
                "category": "safe",
                "language": lang,
                "tier_used": "Tier 1 (Conversational Guardrail)",
                "reason": "Classified safe (conversational pronoun/greeting)",
                "latency_ms": round(latency, 2),
            }
            self._save_cache(cache_key, result)
            self._update_stats(latency)
            return result

        # -------------------------------------------------------------
        # TIER 2: Fast TF-IDF ML Classifier (< 5ms)
        # -------------------------------------------------------------
        X_vec = self.vectorizer.transform([cleaned_text])
        ml_probs = self.tier2_model.predict_proba(X_vec)[0]
        toxic_prob = float(ml_probs[1])

        # High confidence safe threshold (< 0.15) -> return Safe immediately
        if toxic_prob < 0.15:
            with self._lock:
                self.stats["tier2_ml_hits"] += 1
            latency = (time.perf_counter() - start_time) * 1000.0
            result = {
                "text": raw_text,
                "is_harmful": False,
                "score": round(toxic_prob, 3),
                "category": "safe",
                "language": lang,
                "tier_used": "Tier 2 (Fast TF-IDF Classifier)",
                "reason": f"Classified safe with {round((1 - toxic_prob) * 100, 1)}% confidence",
                "latency_ms": round(latency, 2),
            }
            self._save_cache(cache_key, result)
            self._update_stats(latency)
            return result

        # -------------------------------------------------------------
        # TIER 3: Contextual Ensemble + optional Transformer (10 - 30ms)
        # -------------------------------------------------------------
        with self._lock:
            self.stats["tier3_transformer_hits"] += 1
        ensemble_probs = self.tier3_ensemble.predict_proba(X_vec)[0]
        final_score = float(ensemble_probs[1])

        transformer_score = self._transformer_toxicity(cleaned_text, lang)
        if transformer_score is not None:
            final_score = (final_score + transformer_score) / 2.0

        is_harmful = final_score >= sensitivity_threshold
        category = self._guess_category(cleaned_text) if is_harmful else "safe"

        latency = (time.perf_counter() - start_time) * 1000.0
        tier_label = ("Tier 3 (Contextual Ensemble + Transformer)"
                      if transformer_score is not None
                      else "Tier 3 (Contextual Subword Ensemble)")
        result = {
            "text": raw_text,
            "is_harmful": is_harmful,
            "score": round(final_score, 3),
            "category": category,
            "language": lang,
            "tier_used": tier_label,
            "reason": f"Deep contextual classifier calculated {round(final_score * 100, 1)}% toxicity probability",
            "latency_ms": round(latency, 2),
        }

        self._save_cache(cache_key, result)
        self._update_stats(latency)
        return result

    # ------------------------------------------------------------------
    # Batch prediction (vectorized ML tiers)
    # ------------------------------------------------------------------
    def predict_batch(self, text_list: List[Dict[str, Any]], sensitivity_threshold: float = 0.6) -> List[Dict[str, Any]]:
        """
        Batch prediction optimized for Chrome Extension DOM sweeps.
        Cache/lexicon tiers run per item; TF-IDF transform and ML predict_proba run ONCE.
        """
        start_time = time.perf_counter()
        results: List[Optional[Dict[str, Any]]] = [None] * len(text_list)

        # (idx, node_id, raw, cleaned, lang, cache_key)
        pending: List[Tuple[int, str, str, str, str, str]] = []
        first_seen: Dict[str, int] = {}
        deferred: List[Tuple[int, str, str]] = []

        with self._lock:
            self.stats["total_queries"] += len(text_list)

        for idx, item in enumerate(text_list):
            node_id = item.get("id", f"el_{idx}")
            raw_text = item.get("text", "") or ""
            text = raw_text.strip()
            if not text:
                results[idx] = {**self._empty_result(text), "id": node_id}
                continue
            cache_key = f"{self._hash_text(text)}_{sensitivity_threshold}"
            cached = self._cache_get(cache_key)
            if cached is not None:
                with self._lock:
                    self.stats["tier0_cache_hits"] += 1
                cached = dict(cached)
                cached["id"] = node_id
                cached["tier_used"] = "Tier 0 (LRU Cache)"
                results[idx] = cached
                continue
            if cache_key in first_seen:
                deferred.append((idx, node_id, cache_key))
                continue
            first_seen[cache_key] = idx
            cleaned_text, lang, _ = preprocess_text(raw_text)
            pending.append((idx, node_id, raw_text, cleaned_text, lang, cache_key))

        def resolve_deferred():
            for d_idx, d_node_id, d_key in deferred:
                src_idx = first_seen.get(d_key)
                if src_idx is None or results[src_idx] is None:
                    continue
                clone = dict(results[src_idx])
                clone["id"] = d_node_id
                clone["tier_used"] = "Tier 0 (LRU Cache)"
                with self._lock:
                    self.stats["tier0_cache_hits"] += 1
                results[d_idx] = clone

        if not pending:
            resolve_deferred()
            self._update_stats((time.perf_counter() - start_time) * 1000.0)
            return [r for r in results if r is not None]

        # Tier 1: Lexicon Filter & Conversational Guardrail
        still_pending: List[Tuple[int, str, str, str, str, str]] = []
        for idx, node_id, raw_text, cleaned_text, lang, cache_key in pending:
            lexicon_res = fast_lexicon_check(cleaned_text, lang)
            if lexicon_res and lexicon_res[1] >= sensitivity_threshold:
                _, score, category, matched_word, reason = lexicon_res
                with self._lock:
                    self.stats["tier1_lexicon_hits"] += 1
                result = {
                    "id": node_id,
                    "text": raw_text,
                    "is_harmful": True,
                    "score": round(score, 3),
                    "category": category,
                    "language": lang,
                    "tier_used": "Tier 1 (Lexicon/Pattern Filter)",
                    "matched_keyword": matched_word,
                    "reason": reason,
                    "latency_ms": 0.0,
                }
                results[idx] = result
                self._save_cache(cache_key, result)
            elif is_purely_benign_conversational(cleaned_text):
                with self._lock:
                    self.stats["tier1_lexicon_hits"] += 1
                result = {
                    "id": node_id,
                    "text": raw_text,
                    "is_harmful": False,
                    "score": 0.05,
                    "category": "safe",
                    "language": lang,
                    "tier_used": "Tier 1 (Conversational Guardrail)",
                    "reason": "Classified safe (conversational pronoun/greeting)",
                    "latency_ms": 0.0,
                }
                results[idx] = result
                self._save_cache(cache_key, result)
            else:
                still_pending.append((idx, node_id, raw_text, cleaned_text, lang, cache_key))

        if not still_pending:
            resolve_deferred()
            total_ms = (time.perf_counter() - start_time) * 1000.0
            for r in results:
                if r is not None and r.get("latency_ms") == 0.0:
                    r["latency_ms"] = round(total_ms / max(len(results), 1), 2)
            self._update_stats(total_ms)
            return [r for r in results if r is not None]

        # Tier 2: Vectorized ML Transform & Proba
        cleaned_texts = [p[3] for p in still_pending]
        X_vec = self.vectorizer.transform(cleaned_texts)
        probs2 = self.tier2_model.predict_proba(X_vec)[:, 1]

        tier2_indices: List[int] = []
        for pos, (idx, node_id, raw_text, cleaned_text, lang, cache_key) in enumerate(still_pending):
            toxic_prob = float(probs2[pos])
            if toxic_prob < 0.15:
                with self._lock:
                    self.stats["tier2_ml_hits"] += 1
                results[idx] = {
                    "id": node_id,
                    "text": raw_text,
                    "is_harmful": False,
                    "score": round(toxic_prob, 3),
                    "category": "safe",
                    "language": lang,
                    "tier_used": "Tier 2 (Fast TF-IDF Classifier)",
                    "reason": f"Classified safe with {round((1 - toxic_prob) * 100, 1)}% confidence",
                    "latency_ms": 0.0,
                }
                self._save_cache(cache_key, results[idx])
            else:
                tier2_indices.append(pos)

        if not tier2_indices:
            resolve_deferred()
            total_ms = (time.perf_counter() - start_time) * 1000.0
            for r in results:
                if r is not None and r.get("latency_ms") == 0.0:
                    r["latency_ms"] = round(total_ms / max(len(results), 1), 2)
            self._update_stats(total_ms)
            return [r for r in results if r is not None]

        # Tier 3: Ensemble
        tier3_positions = tier2_indices
        X3 = X_vec[tier3_positions]
        probs3 = self.tier3_ensemble.predict_proba(X3)[:, 1]
        with self._lock:
            self.stats["tier3_transformer_hits"] += len(tier3_positions)

        total_batch_ms = (time.perf_counter() - start_time) * 1000.0

        for local_pos, pos in enumerate(tier3_positions):
            idx, node_id, raw_text, cleaned_text, lang, cache_key = still_pending[pos]
            final_score = float(probs3[local_pos])

            transformer_score = self._transformer_toxicity(cleaned_text, lang)
            tier_label = "Tier 3 (Contextual Subword Ensemble)"
            if transformer_score is not None:
                final_score = (final_score + transformer_score) / 2.0
                tier_label = "Tier 3 (Contextual Ensemble + Transformer)"

            is_harmful = final_score >= sensitivity_threshold
            category = self._guess_category(cleaned_text) if is_harmful else "safe"
            results[idx] = {
                "id": node_id,
                "text": raw_text,
                "is_harmful": is_harmful,
                "score": round(final_score, 3),
                "category": category,
                "language": lang,
                "tier_used": tier_label,
                "reason": f"Deep contextual classifier calculated {round(final_score * 100, 1)}% toxicity probability",
                "latency_ms": round(total_batch_ms / max(len(results), 1), 2),
            }
            self._save_cache(cache_key, results[idx])

        resolve_deferred()
        self._update_stats(total_batch_ms)
        return [r for r in results if r is not None]


def joblib_load(filename: str):
    import joblib
    target = MODELS_DIR / filename
    return joblib.load(str(target))
