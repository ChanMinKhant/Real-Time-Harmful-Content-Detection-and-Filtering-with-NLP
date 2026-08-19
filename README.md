# 🛡️ Real-Time Harmful Content Blur Guard (NLP + Chrome Extension)

Bilingual (English & Myanmar) real-time harmful content detector that automatically blurs toxic, cyberbullying, hate speech, and profanity elements during web browsing.

---

## 🌟 Key Features

1. **Bilingual NLP Support**: Accurate detection for both **English** and **Myanmar (Burmese Unicode)** scripts.
2. **Ultra-Fast Cascading Pipeline**: 
   - **Tier 0**: In-Memory LRU Cache ($< 0.1\text{ms}$)
   - **Tier 1**: Lexicon & Syllable Pattern Filter ($< 1\text{ms}$)
   - **Tier 2**: Character N-gram TF-IDF ML Classifier ($< 5\text{ms}$)
   - **Tier 3**: Deep Contextual Transformer Model ($20 - 40\text{ms}$)
3. **Interactive UI**:
   - Modern frosted glass blur effect (`backdrop-filter`).
   - Warning badge: `⚠️ HARMFUL DETECTED (Confidence %)`.
   - **"👁️ Reveal"** to unblur and **"🔒 Re-blur"** button.
4. **Manifest V3 Chrome Extension**:
   - Live settings popup (Sensitivity slider, Category toggles, Real-time stats).
   - Instant in-popup NLP tester.
5. **Interactive Demo Page (`demo/demo.html`)**:
   - Mock social media feed with preset tests and dynamic comment posting for live presentations.

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
🛡️ Harmful Content NLP Backend (Flask) Running on http://127.0.0.1:5000
📡 Ready to accept requests from Chrome Extension...
```

---

### Step 2: Load Chrome Extension into Google Chrome

1. Open Google Chrome and navigate to `chrome://extensions/`
2. Enable **"Developer mode"** in the top right corner.
3. Click **"Load unpacked"** (top left).
4. Select the `extension` folder inside this project directory (`/Users/mac/.gemini/antigravity/scratch/harmful_content_blur_nlp/extension`).
5. The **Harmful Content Blurry Guard** extension icon 🛡️ will appear in your Chrome toolbar!

---

### Step 3: Run the Live Presentation Demo

1. Open `demo/demo.html` in Chrome:
   - Either double click `demo/demo.html` or drag it into Chrome.
2. You will instantly see harmful English & Myanmar comments blurred with warning badges!
3. Click the preset buttons (`+ Add MM Toxic`, `+ Add EN Cyberbullying`, etc.) or type a live comment in the box and press **"Post Comment"** to see real-time detection in action!
4. Click on the extension icon in the toolbar to adjust the sensitivity slider or test individual sentences.

---

## 📂 Project Structure

```text
harmful_content_blur_nlp/
├── backend/
│   ├── app.py              # Flask Server with RESTful APIs
│   ├── pipeline.py         # Cascading 4-Tier NLP Classification Engine
│   ├── normalizer.py       # Myanmar Unicode & Syllable Break + English Normalizer
│   ├── lexicon_mm.py       # Curated Myanmar & English Toxic Dictionaries
│   ├── requirements.txt    # Dependencies
│   └── venv/               # Python Virtual Environment
├── extension/
│   ├── manifest.json       # Chrome Manifest V3 configuration
│   ├── content.js          # DOM Scraper, Batch Dispatcher, & Blur Engine
│   ├── content.css         # Modern Blur & Warning Badge styling
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
