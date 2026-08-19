# 🎓 NLP Project Presentation Guide & Academic Defense Document

**Project Title:** Real-Time Harmful Content Detection & Element Blurring System using Cascading NLP Pipeline  
**Target Languages:** English & Myanmar (ဗမာစာ)  
**Tech Stack:** Python (Flask), Scikit-Learn, Hugging Face Transformers, JavaScript (Chrome Extension Manifest V3)

---

## 📑 Slide-by-Slide Presentation Structure (Slide Outline)

### **Slide 1: Title & Introduction (ခေါင်းစဉ်နှင့် မိတ်ဆက်)**
- **Title:** Real-Time Bilingual Harmful Content Detection & UI Blurring Guard
- **Presenter:** [Your Name / Team Members]
- **Problem Statement (ပြဿနာ):**
  - ဆိုရှယ်မီဒီယာနှင့် ဝဘ်ဆိုက်များတွင် Cyberbullying, Hate Speech, Toxicity နှင့် Profanity (ရိုင်းစိုင်းသော အမုန်းစကားများ) များပြားလာခြင်း။
  - အထူးသဖြင့် မြန်မာဘာသာ (Burmese Unicode) အတွက် Real-time အကာအကွယ်ပေးနိုင်သော စနစ်များ ရှားပါးနေသေးခြင်း။
  - **Our Goal:** User များ Web ကြည့်ရှုနေစဉ် မလိုလားအပ်သော စိတ်အနှောင့်အယှက်ဖြစ်စေမည့် စာသားများကို AI ဖြင့် အချိန်နှင့်တပြေးညီ သိရှိပြီး HTML Element ကို အလိုအလျောက် **Blur** ပြုလုပ်ပေးခြင်း။

---

### **Slide 2: System Architecture & Workflow (စနစ်တည်ဆောက်ပုံ)**
- **Client-Server Architecture:**
  1. **Chrome Extension (Frontend)**: Web Page ရဲ့ DOM Elements များကို Scan ဖတ်ပြီး စာသားများကို Batch ပြုလုပ်ကာ Backend သို့ ပေးပို့သည်။
  2. **Python Flask NLP Server (Backend)**: စာသားများကို NLP Pipeline ဖြင့် စစ်ဆေးကာ Toxicity Score နှင့် Categories များကို ပြန်လည်ပေးပို့သည်။
  3. **Interactive UI Action**: Harmful ဖြစ်ပါက Element ကို Blur လုပ်ပြီး `⚠️ Harmful Content (Click to Reveal)` badge လေး ဖော်ပြပေးသည်။

---

### **Slide 3: Key NLP Concept 1 - Text Preprocessing & Myanmar Syllable Breaking**
- **English Preprocessing:**
  - Case Folding, Whitespace Normalization, Repeated Character Reduction (e.g. `sooooo bad` -> `soo bad`).
- **Myanmar Unicode Preprocessing & Syllable Segmentation:**
  - **Unicode Normalization (NFC):** Reordered vowels (ဥပမာ 'ေ' အရှေ့ရောက်နေခြင်း), duplicate diacritics (အသတ် နှစ်ထပ်ဖြစ်နေခြင်း) များကို Standard Canonical Order သို့ ပြင်ဆင်ခြင်း။
  - **Rule-based Syllable Breaking:** ဗျည်း `[က-အ]`၊ သရ၊ ဗျည်းတွဲ (Medials ျ ြ ွ ှ) နှင့် အသတ် (Killer ်) စည်းမျဉ်းများအပေါ် အခြေခံ၍ စာကြောင်းများကို Syllable များအဖြစ် ခွဲခြမ်းစိတ်ဖြာခြင်း။
  $$\text{Regex Pattern: } (?<![\u103A\u1039])([\u1000-\u1021\u1023-\u102A\u103F\u104E](?:[\u1039][\u1000-\u1021])*(?:[\u103B-\u103E])*(?:[\u102B-\u1035\u1031\u1032])*(?:[\u1036\u1037\u1038\u103A])*)$$
  - *ဥပမာ:* `မင်္ဂလာပါ` $\rightarrow$ `['မင်္ဂ', 'လာ', 'ပါ']`

---

### **Slide 4: Key NLP Concept 2 - Cascading Multi-Tier Pipeline (Speed vs Accuracy Trade-off)**
- **The Real-Time Challenge:**
  - Deep Learning Transformer Models (BERT/RoBERTa) များသည် အလွန် တိကျသော်လည်း Inference တစ်ကြိမ်လျှင် `300ms - 500ms` ကြာမြင့်နိုင်သည်။
  - ဝဘ်စာမျက်နှာတစ်ခုတွင် Comment အခု ၁၀၀ ရှိပါက စက္ကန့် ၃၀ မှ ၅၀ အထိ ကြာမြင့်သွားနိုင်ပြီး User Experience ကို အလွန် ထိခိုက်စေသည်။
- **Our Cascading Solution (အဆင့် ၄ ဆင့် ခွဲခြားစစ်ဆေးခြင်း):**
  1. **Tier 0 (In-Memory LRU Cache):** စစ်ပြီးသား စာသားများကို Hash ဖြင့် မှတ်ထားပြီး ချက်ချင်း ပြန်ထုတ်ပေးသည် ($< 0.1\text{ms}$ latency)။
  2. **Tier 1 (Fast Lexicon & Regex Matcher):** တိုက်ရိုက်ဆဲဆိုမှုနှင့် အမုန်းစကား သိသာသော စကားလုံးများကို $< 1\text{ms}$ အတွင်း ချက်ချင်း ဖမ်းယူသည်။
  3. **Tier 2 (Fast TF-IDF + Character N-Gram Classifier):** Subword n-gram features များဖြင့် သာမန် Safe စာသားများကို $< 5\text{ms}$ အတွင်း ခွဲခြားပေးသည်။
  4. **Tier 3 (Deep Transformer BERT):** ရှုပ်ထွေးသော၊ သွယ်ဝိုက်သော Contextual Bullying များကိုသာ Deep Neural Network ထံ ပို့ဆောင်စစ်ဆေးသည်။
- **ရလဒ်:** Average Latency ကို **sub-5ms** အထိ လျှော့ချနိုင်ပြီး Accuracy ကို အမြင့်ဆုံး ထိန်းသိမ်းထားနိုင်သည်။

---

### **Slide 5: Harmful Categories & Detection Scope**
1. **Cyberbullying & Harassment:** ရုပ်ဆင်းသွင်ပြင်လှောင်ပြောင်ခြင်း၊ သေခိုင်းခြင်း၊ ခြိမ်းခြောက်ခြင်း။
2. **Hate Speech:** လူမျိုး၊ ဘာသာ၊ ဇာတိအပေါ် အခြေခံ၍ ခွဲခြားတိုက်ခိုက်ခြင်း။
3. **Severe Toxicity & Profanity:** ရိုင်းစိုင်းသော ဆဲဆိုစကားလုံးများ။
4. **Insults & Defamation:** ဂုဏ်သိက္ခာကျဆင်းစေသော နှိမ်ချစကားလုံးများ။

---

### **Slide 6: Live Demonstration & UI Features (လက်တွေ့ သရုပ်ပြခြင်း)**
1. **Flask NLP Server** ကို Run ပြသခြင်း (`python app.py`)။
2. **Chrome Extension** ကို ဖွင့်ပြီး Sensitivity Slider ပြောင်းလဲပြသခြင်း။
3. **Demo Social Media Feed (`demo.html`)** တွင်:
   - English Toxic Comments များ အလိုအလျောက် Blur ဖြစ်သွားပုံ။
   - Myanmar Hate Speech/Cyberbullying Comments များ Blur ဖြစ်သွားပုံ။
   - Positive/Safe စာသားများ ပုံမှန်အတိုင်း ပေါ်နေပုံ။
   - `👁️ Reveal` ခလုတ်ကို နှိပ်၍ Unblur လုပ်ကြည့်နိုင်ပြီး `🔒 Re-blur` ပြန်လုပ်နိုင်ပုံ။
   - Live Comment ရိုက်ထည့်လိုက်သည်နှင့် စက္ကန့်ပိုင်းအတွင်း ချက်ချင်း Blur ဖြစ်သွားပုံ။

---

### **Slide 7: Performance Evaluation & Future Work**
- **Performance Summary:**
  - Average Batch Response Time: **< 10ms**
  - Cache Hit Ratio: **> 85%** on continuous browsing
  - Multilingual Support: English + Myanmar (Unicode)
- **Future Improvements:**
  - Multimodal Detection (Images & Memes text OCR integration)
  - On-device ONNX runtime in browser extension without backend

---

## 🎤 Presentation Speaking Script (တင်ပြရာတွင် ပြောရန် Script)

> **(Opening - မိတ်ဆက်):**  
> "မင်္ဂလာပါ ဆရာများနှင့် သူငယ်ချင်းတို့ခင်ဗျာ။ ကျွန်တော်တို့ ဒီနေ့ တင်ပြမယ့် NLP Project ကတော့ **'Real-Time Harmful Content Detection & Element Blurring System'** ဖြစ်ပါတယ်။"

> **(Problem & Motivation):**  
> "ယနေ့ခေတ် Social Media နဲ့ Web ပေါ်မှာ Cyberbullying နဲ့ Hate Speech တွေက လူငယ်တွေနဲ့ သုံးစွဲသူတွေရဲ့ စိတ်ကျန်းမာရေးကို နေ့စဉ် ခြိမ်းခြောက်နေပါတယ်။ ဒီပြဿနာကို ဖြေရှင်းဖို့အတွက် ကျွန်တော်တို့က Web Browsing လုပ်နေစဉ်မှာတင် Harmful စာသားတွေကို NLP နဲ့ စစ်ဆေးပြီး အဆိုပါ HTML element တွေကို အလိုအလျောက် Blur လုပ်ပေးမယ့် Browser Extension စနစ်တစ်ခုကို တည်ဆောက်ခဲ့ပါတယ်။"

> **(NLP Challenges & Performance):**  
> "ဒီ Project မှာ အဓိက စိန်ခေါ်မှု နှစ်ခု ရှိပါတယ် - ပထမတစ်ခုက **'မြန်မာစာ (Burmese Unicode) Preprocessing နဲ့ Syllable Break'** ဖြစ်ပြီး ဒုတိယတစ်ခုကတော့ Web Page မနှေးကွေးစေဖို့ **'Real-Time Performance (Low Latency)'** ဖြစ်ပါတယ်။ Transformer တွေချည်း သုံးရင် နှေးကွေးနိုင်တာကြောင့် ကျွန်တော်တို့က **Cascading Multi-Tier Pipeline (LRU Cache $\rightarrow$ Lexicon $\rightarrow$ TF-IDF $\rightarrow$ Transformer)** ကို အသုံးပြုပြီး Response time ကို 5ms အောက် ရရှိအောင် စွမ်းဆောင်ထားပါတယ်။"

> **(Live Demo):**  
> "အခု ကျွန်တော်တို့ရဲ့ လက်တွေ့ Demo ကို ပြသပါမယ်ခင်ဗျာ..."
