"""
Lexical Dictionaries and Regex Patterns for Tier 1 Fast Matching (Myanmar & English).
Supports multi-category toxicity detection:
- Hate Speech (လူမျိုး/ဘာသာ/ခွဲခြားမှု)
- Cyberbullying & Harassment (အနိုင်ကျင့်စော်ကားမှု/ခြိမ်းခြောက်မှု)
- Severe Toxicity & Profanity (ဆဲဆိုရိုင်းစိုင်းသော စကားလုံးများ)
- Insults & Defamation (သိက္ခာချ နှိမ်ချသော စကားလုံးများ)

Loads unified rules from `shared/rules.json` with an inline fallback.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from normalizer import normalize_myanmar_unicode, segment_myanmar_syllables

# Category readable labels
DEFAULT_CATEGORY_LABELS = {
    "hate_speech": "Hate Speech (အမုန်းစကား)",
    "cyberbullying": "Cyberbullying (အနိုင်ကျင့်စော်ကားမှု)",
    "profanity": "Profanity / Toxic (ဆဲဆိုရိုင်းစိုင်းမှု)",
    "insult": "Insult (စော်ကားနှိမ်ချမှု)"
}

# Fallback Myanmar Lexicon
FALLBACK_MM_LEXICON = {
    "hate_speech": [
        "ကုလား", "ကုလားဆိုး", "တရုတ်ခွေး", "ခွေးကုလား", "ဘာသာဖျက်",
        "မိစ္ဆာဒိဌိ", "ခွေးမျိုး", "ကုလားဖြူ", "ကုလားမဲ", "လူမျိုးတုံး",
        "မျိုးမစစ်", "တိုင်းတစ်ပါးသားခွေး", "ကုလားဂျင်း"
    ],
    "cyberbullying": [
        "သေလိုက်ပါလား", "သွားသေလိုက်", "မင်းအသက်ရှင်နေတာအပိုပဲ", "ရုပ်ကိုကဆိုးတာ",
        "မျက်နှာမွဲ", "အရုပ်ဆိုး", "အဆီပုတ်", "ဖက်တီး", "ဝက်လိုကောင်", "ဝက်မ",
        "နုံချာလိုက်တာ", "ငတုံး", "မအ", "မအေဘေး", "လဒ", "ငကြောင်", "အသုံးမကျတဲ့ကောင်",
        "အသုံးမကျတဲ့ဟာ", "မျက်နှာပြောင်", "မရှက်ဘူးလား", "ရွံစရာကောင်းလိုက်တာ"
    ],
    "profanity": [
        "လိုး", "လိုးမ", "လိုးမသား", "မအေလိုး", "မအေလိုးသား", "ဖာသည်", "ဖာသယ်",
        "ဖာခေါင်း", "ဖာသည်မ", "ခွေးမသား", "ခွေးသူတောင်းစား", "လီး", "လီးပဲ", "လီးလား",
        "စောက်ရမ်း", "စောက်ပတ်", "စောက်ဖုတ်", "စောက်ရူး", "စောက်ကျိုးနည်း",
        "စောက်သုံးမကျ", "စောက်ချိုး", "စောက်ပေါ", "ခွေးလိုကောင်", "ခွေးမ", "ခွေးသား"
    ],
    "insult": [
        "လူယုတ်မာ", "သူတောင်းစား", "သူခိုး", "လိမ်ညာတဲ့ကောင်", "ငနပိ",
        "တောသား", "အရူး", "ရူးနေလား", "အပေါစား", "အောက်တန်းစား", "အဆင့်မရှိတဲ့ကောင်",
        "လိမ်ဖုတ်", "ကောက်ကျစ်တဲ့ကောင်", "ကလေကချေ"
    ]
}

# Fallback English Lexicon
FALLBACK_EN_LEXICON = {
    "hate_speech": [
        "nigger", "nigga", "faggot", "kike", "chink", "wetback", "retard",
        "white trash", "islamophobic", "terrorist", "subhuman", "filthy immigrant"
    ],
    "cyberbullying": [
        "kill yourself", "kys", "die already", "go die", "nobody likes you",
        "ugly freak", "worthless piece of shit", "waste of oxygen", "fat ugly pig",
        "loser", "you are pathetic", "disgusting pig", "jump off a cliff"
    ],
    "profanity": [
        "fuck", "fucking", "fucked", "motherfucker", "bitch", "bitches",
        "cunt", "asshole", "bastard", "dick", "pussy", "shit", "bullshit",
        "cock", "slut", "whore", "dumbass", "dipshit", "jackass"
    ],
    "insult": [
        "idiot", "moron", "stupid", "imbecile", "trash", "scumbag",
        "clown", "garbage", "pathetic loser", "brainless", "incompetent"
    ]
}

FALLBACK_OBF_EXTRA = {
    'a': '4@', 'e': '3', 'i': '1!|', 'o': '0', 'u': '@*_',
    's': '$5', 't': '7+', 'l': '1|', 'g': '9', 'b': '8', 'c': '<',
}


def _load_shared_rules() -> Tuple[Dict[str, List[str]], Dict[str, List[str]], Dict[str, str], Dict[str, str]]:
    shared_path = Path(__file__).resolve().parent.parent / "shared" / "rules.json"
    if shared_path.exists():
        try:
            with open(shared_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                mm = data.get("myanmar_lexicon", FALLBACK_MM_LEXICON)
                en = data.get("english_lexicon", FALLBACK_EN_LEXICON)
                obf = data.get("leetspeak", {}).get("obfuscation_patterns", FALLBACK_OBF_EXTRA)
                labels = data.get("categories", DEFAULT_CATEGORY_LABELS)
                return mm, en, obf, labels
        except Exception:
            pass
    return FALLBACK_MM_LEXICON, FALLBACK_EN_LEXICON, FALLBACK_OBF_EXTRA, DEFAULT_CATEGORY_LABELS


MYANMAR_LEXICON, ENGLISH_LEXICON, OBF_EXTRA, CATEGORY_LABELS = _load_shared_rules()


def _syllable_join(text: str) -> str:
    return " ".join(segment_myanmar_syllables(normalize_myanmar_unicode(text)))


def _compile_en_patterns(lexicon_dict: Dict[str, List[str]]) -> Dict[str, re.Pattern]:
    compiled = {}
    for category, words in lexicon_dict.items():
        escaped_words = [re.escape(w) for w in sorted(dict.fromkeys(words), key=len, reverse=True)]
        pattern_str = r'\b(?:' + '|'.join(escaped_words) + r')\b'
        compiled[category] = re.compile(pattern_str, re.IGNORECASE)
    return compiled


def _compile_mm_patterns(lexicon_dict: Dict[str, List[str]]) -> Dict[str, re.Pattern]:
    compiled = {}
    for category, words in lexicon_dict.items():
        token_patterns = []
        for word in dict.fromkeys(words):
            syls = segment_myanmar_syllables(normalize_myanmar_unicode(word))
            if not syls:
                continue
            joined = r'\s+'.join(re.escape(s) for s in syls)
            token_patterns.append(r'(?<!\S)' + joined + r'(?!\S)')
        if token_patterns:
            token_patterns.sort(key=len, reverse=True)
            compiled[category] = re.compile('|'.join(token_patterns))
    return compiled


def _tolerant_char(ch: str) -> str:
    low = ch.lower()
    if not low.isalpha():
        return re.escape(ch)
    return '[' + low + OBF_EXTRA.get(low, '') + ']+'


def _compile_en_tolerant_patterns(lexicon_dict: Dict[str, List[str]]) -> Dict[str, re.Pattern]:
    compiled = {}
    for category, words in lexicon_dict.items():
        bodies = []
        for word in dict.fromkeys(words):
            parts = [_tolerant_char(c) if c != ' ' else r'\s+' for c in word]
            bodies.append(''.join(parts))
        compiled[category] = re.compile(r'\b(?:' + '|'.join(bodies) + r')\b')
    return compiled


MM_PATTERNS = _compile_mm_patterns(MYANMAR_LEXICON)
EN_PATTERNS = _compile_en_patterns(ENGLISH_LEXICON)
EN_TOLERANT_PATTERNS = _compile_en_tolerant_patterns(ENGLISH_LEXICON)
OBF_SIGNAL_RE = re.compile(r'[0-9@#$+|<!*]')


def _match_en_category(patterns: Dict[str, re.Pattern], text: str,
                        severe_score: float) -> Optional[Tuple[bool, float, str, str, str]]:
    for cat, pattern in patterns.items():
        match = pattern.search(text)
        if match:
            matched_word = match.group(0)
            score = severe_score if cat in ('hate_speech', 'profanity') else 0.88
            label = CATEGORY_LABELS.get(cat, cat.title())
            return (
                True,
                score,
                cat,
                matched_word,
                f"Detected harmful keyword '{matched_word}' [{label}]"
            )
    return None


def fast_lexicon_check(text: str, language: str) -> Optional[Tuple[bool, float, str, str, str]]:
    """
    Tier 1 Ultra-fast Lexicon Filter (boundary-aware).
    Returns:
    (is_harmful, confidence_score, category, matched_keyword, reason) or None if no match.
    """
    if not text:
        return None

    # Check Myanmar patterns if language is 'my' or 'mixed'
    if language in ('my', 'mixed'):
        joined_text = _syllable_join(text)
        for cat, pattern in MM_PATTERNS.items():
            match = pattern.search(joined_text)
            if match:
                matched_word = re.sub(r'\s+', '', match.group(0))
                score = 0.95 if cat in ('hate_speech', 'profanity') else 0.85
                label = CATEGORY_LABELS.get(cat, cat.title())
                return (
                    True,
                    score,
                    cat,
                    matched_word,
                    f"Detected harmful keyword '{matched_word}' [{label}]"
                )

    # Check English patterns if language is 'en' or 'mixed'
    if language in ('en', 'mixed'):
        en_result = _match_en_category(EN_PATTERNS, text, 0.96)
        if not en_result and OBF_SIGNAL_RE.search(text):
            en_result = _match_en_category(EN_TOLERANT_PATTERNS, text, 0.90)
        if en_result:
            return en_result

    return None


def get_lexicon_summary() -> Dict[str, int]:
    """Returns total word counts per category for diagnostics and stats API."""
    return {
        "categories_count": len(CATEGORY_LABELS),
        "myanmar_keywords_count": sum(len(v) for v in MYANMAR_LEXICON.values()),
        "english_keywords_count": sum(len(v) for v in ENGLISH_LEXICON.values()),
    }
