# 🛡️ Real-Time Harmful Content Blur Guard (NLP + Chrome Extension)

Bilingual (English & Myanmar) real-time harmful content detector that automatically blurs toxic, cyberbullying, hate speech, and profanity elements during web browsing.

---

## 🌟 Key Features

1. **Bilingual NLP Support**: Accurate detection for both **English** and **Myanmar (Burmese Unicode)** scripts.
2. **Ultra-Fast Cascading Pipeline**: 
   - **Tier 0**: In-Memory LRU Cache ($< 0.1\text{ms}$)
   - **Tier 1**: Boundary-Aware Lexicon & Syllable Pattern Filter ($< 1\text{ms}$)
   - **Tier 2**: Character N-gram TF-IDF ML Classifier ($< 5\text{ms}$)
   - **Tier 3**: Contextual Ensemble + Optional English Transformer (lazy-loaded; falls back gracefully when torch/transformers are unavailable)
3. **Interactive UI**:
   - Modern frosted glass blur effect (`backdrop-filter`).
   - Warning badge with category and confidence score.
   - Complete hierarchy double-click permanent reveal and locked link/button protection.
4. **Manifest V3 Chrome Extension**:
   - Modular architecture (`rules.js`, `api_client.js`, `blur_manager.js`, `dom_scanner.js`, `content.js`).
   - `requestIdleCallback` debounced DOM scanning for 60fps scrolling.
   - Live settings popup (Sensitivity slider, Category toggles, Real-time stats, and Instant in-popup NLP tester).
5. **Interactive Demo Page (`demo/demo.html`)**:
   - Mock social media feed with preset tests and dynamic comment posting for live presentations.
6. **Single Source of Truth (`shared/rules.json`)**:
   - Unified lexicon, categories, and leetspeak rules synchronized across Python and Extension.

---

## 🚀 How to Run the Project

### Step 1: Start the Python Flask NLP Backend
Open your terminal in this project directory:

```bash
cd backend
source venv/bin/activate
python app.py
```

You should see:
```text
=======================================================
🛡️  Harmful Content NLP Backend (Flask) Running on http://127.0.0.1:5000
📡  Ready to accept requests from Chrome Extension...
=======================================================
```

---

### Step 2: Load Chrome Extension into Google Chrome

1. Open Google Chrome and navigate to `chrome://extensions/`
2. Enable **"Developer mode"** in the top right corner.
3. Click **"Load unpacked"** (top left).
4. Select the `extension` folder inside this project directory.
5. The **Harmful Content Blurry Guard** extension icon 🛡️ will appear in your Chrome toolbar!

---

### Step 3: Run the Live Presentation Demo

1. Open `demo/demo.html` in Chrome:
   - Either double click `demo/demo.html` or drag it into Chrome.
   - Or visit `http://127.0.0.1:5000/demo` while the backend is running.
2. You will instantly see harmful English & Myanmar comments blurred with warning badges!
3. Click the preset buttons (`+ Add MM Toxic`, `+ Add EN Cyberbullying`, etc.) or type a live comment in the box and press **"Post Comment"** to see real-time detection in action!
4. Click on the extension icon in the toolbar to adjust the sensitivity slider or test individual sentences.

---

## 📂 Project Structure

```text
harmful_content_blur_nlp/
├── shared/
│   └── rules.json          # Single Source of Truth for Bilingual Toxic Lexicon & Rules
├── scripts/
│   └── sync_lexicon.py     # Synchronizes shared/rules.json to Python and Extension
├── backend/
│   ├── app/
│   │   ├── __init__.py     # Flask Application Factory (create_app)
│   │   ├── config.py       # Environment configuration (Dev, Test, Prod)
│   │   ├── schemas.py      # Typed request validation (Single & Batch)
│   │   └── routes/
│   │       ├── api.py      # REST APIs (/api/health, /api/analyze, /api/rules, ...)
│   │       └── views.py    # Web views (/demo)
│   ├── app.py              # Server entrypoint (loopback-bound, fallback port auto-detect)
│   ├── pipeline.py         # Cascading 4-Tier NLP Engine (LRU Cache, ML & Ensemble)
│   ├── normalizer.py       # Myanmar Unicode & Syllable Break + Leetspeak Normalizer
│   ├── lexicon_mm.py       # Boundary-Aware Myanmar & English Matcher
│   ├── dataset.py          # Bilingual Seed Corpus + Deterministic Augmentation
│   ├── train_model.py      # Training Script: split, F1 metrics, joblib artifacts
│   ├── models/             # Trained artifacts + metadata.json
│   ├── tests/              # Pytest suite: schemas, normalizer, lexicon, pipeline, API
│   ├── requirements.txt    # Dependencies
│   └── venv/               # Python Virtual Environment
├── extension/
│   ├── manifest.json       # Chrome Manifest V3 configuration
│   ├── rules.js            # Synced Lexicons & Compiled Rules
│   ├── api_client.js       # Background proxy & resilient HTTP client
│   ├── blur_manager.js     # Blurring, unblurring & interaction lock
│   ├── dom_scanner.js      # TreeWalker DOM Scanner & in-browser Tier 1 matcher
│   ├── content.js          # Main content script orchestrator
│   ├── content.css         # Blur & Badge styling
│   ├── popup/
│   │   ├── popup.html      # Extension Dashboard Popup UI
│   │   ├── popup.css       # Dark theme CSS
│   │   └── popup.js        # Controller & Instant Tester
│   └── icons/              # Extension PNG Icons (16, 48, 128)
├── demo/
│   └── demo.html           # Presentation Demo Feed
├── PRESENTATION_GUIDE.md   # Complete Slide Outline, Script & Academic Defense Guide
└── README.md               # Documentation & Setup Guide
```

---

### Testing & Validation

Run all unit and integration tests:

```bash
cd backend
source venv/bin/activate
pytest -v
```

To validate and re-sync shared rules:

```bash
python scripts/sync_lexicon.py --check
```

To retrain the ML tiers after editing the corpus:

```bash
python backend/train_model.py
```
