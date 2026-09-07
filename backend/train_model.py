"""
Trains the Tier 2 / Tier 3 classifiers on the bilingual dataset and saves
versioned artifacts to backend/models/.

Usage:
    python train_model.py                 # built-in augmented dataset
    python train_model.py --csv data.csv  # optional external CSV (columns: text,label)

Outputs:
    models/vectorizer.joblib
    models/tier2_logreg.joblib
    models/tier3_ensemble.joblib
    models/metadata.json
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import VotingClassifier

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dataset import build_dataset, build_split_dataset, texts_and_labels  # noqa: E402

MODEL_VERSION = "2.1.0"
MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")


def load_external_csv(path: str):
    """Optional: merge an external CSV with 'text' and 'label' columns."""
    texts, labels = [], []
    with open(path, "r", encoding="utf-8") as f:
        header = f.readline().strip().lower().split(",")
        try:
            ti = [h.strip() for h in header].index("text")
            li = [h.strip() for h in header].index("label")
        except ValueError:
            raise SystemExit("CSV must have 'text' and 'label' columns")
        for line in f:
            cols = line.rstrip("\n").split(",")
            if len(cols) <= max(ti, li) or not cols[ti].strip():
                continue
            texts.append(cols[ti].strip())
            labels.append(int(cols[li]))
    return texts, labels


def main():
    train_data, test_data = build_split_dataset(test_size=0.2, seed=42)
    X_train, y_train = texts_and_labels(train_data)
    X_test, y_test = texts_and_labels(test_data)

    if "--csv" in sys.argv:
        path = sys.argv[sys.argv.index("--csv") + 1]
        ext_texts, ext_labels = load_external_csv(path)
        print(f"Merging {len(ext_texts)} external samples from {path}")
        X_train += ext_texts
        y_train += ext_labels

    print(f"Train size: {len(X_train)} (harmful={sum(y_train)}, safe={len(y_train) - sum(y_train)}) | "
          f"Test size: {len(X_test)} (harmful={sum(y_test)}, safe={len(y_test) - sum(y_test)})")

    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(2, 5),
        min_df=2,
        sublinear_tf=True,
    )
    Xv_train = vectorizer.fit_transform(X_train)
    Xv_test = vectorizer.transform(X_test)

    # Tier 2: fast linear classifier with calibrated regularization
    tier2 = LogisticRegression(C=1.5, class_weight="balanced", max_iter=1000, random_state=42)
    tier2.fit(Xv_train, y_train)

    # Tier 3: soft-voting ensemble
    tier3 = VotingClassifier(
        estimators=[
            ("lr", LogisticRegression(C=2.0, class_weight="balanced", max_iter=1000, random_state=42)),
            ("nb", MultinomialNB(alpha=0.3)),
        ],
        voting="soft",
    )
    tier3.fit(Xv_train, y_train)

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------
    print("\n=== Tier 2 (LogisticRegression) ===")
    pred2 = tier2.predict(Xv_test)
    print(classification_report(y_test, pred2, target_names=["safe", "harmful"]))

    print("=== Tier 3 (Voting Ensemble) ===")
    pred3 = tier3.predict(Xv_test)
    report3 = classification_report(y_test, pred3, target_names=["safe", "harmful"])
    print(report3)

    f1_harmful_t2 = f1_score(y_test, pred2, pos_label=1)
    f1_harmful_t3 = f1_score(y_test, pred3, pos_label=1)
    print(f"F1(harmful): tier2={f1_harmful_t2:.3f}  tier3={f1_harmful_t3:.3f}")

    # ------------------------------------------------------------------
    # Persist artifacts
    # ------------------------------------------------------------------
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(vectorizer, os.path.join(MODELS_DIR, "vectorizer.joblib"))
    joblib.dump(tier2, os.path.join(MODELS_DIR, "tier2_logreg.joblib"))
    joblib.dump(tier3, os.path.join(MODELS_DIR, "tier3_ensemble.joblib"))

    metadata = {
        "model_version": MODEL_VERSION,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset_size": len(X_train) + len(X_test),
        "train_size": len(X_train),
        "test_size": len(X_test),
        "f1_harmful_tier2": round(float(f1_harmful_t2), 4),
        "f1_harmful_tier3": round(float(f1_harmful_t3), 4),
        "vectorizer": {
            "analyzer": "char_wb",
            "ngram_range": [2, 5],
            "sublinear_tf": True,
        },
    }
    with open(os.path.join(MODELS_DIR, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Artifacts saved to {MODELS_DIR}")


if __name__ == "__main__":
    start = time.perf_counter()
    main()
    print(f"Training finished in {time.perf_counter() - start:.1f}s")
