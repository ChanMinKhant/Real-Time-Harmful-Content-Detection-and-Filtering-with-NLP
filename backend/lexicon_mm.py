"""
Lexical Dictionaries and Regex Patterns for Tier 1 Fast Matching (Myanmar & English).
Supports multi-category toxicity detection:
- Hate Speech (လူမျိုး/ဘာသာ/ခွဲခြားမှု)
- Cyberbullying & Harassment (အနိုင်ကျင့်စော်ကားမှု/ခြိမ်းခြောက်မှု)
- Severe Toxicity & Profanity (ဆဲဆိုရိုင်းစိုင်းသော စကားလုံးများ)
- Insults & Defamation (သိက္ခာချ နှိမ်ချသော စကားလုံးများ)
"""

import re
from typing import Dict, List, Tuple, Optional

# Myanmar Lexicon by Category
MYANMAR_LEXICON = {
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
        "စောက်သုံးမကျ", "စောက်ချိုး", "စောက်ပေါ", "လီးပဲ", "ခွေးလိုကောင်", "ခွေးမ", "ခွေးသား"
    ],
    "insult": [
        "လူယုတ်မာ", "သူတောင်းစား", "သူခိုး", "လိမ်ညာတဲ့ကောင်", "ငနပိ",
        "တောသား", "အရူး", "ရူးနေလား", "အပေါစား", "အောက်တန်းစား", "အဆင့်မရှိတဲ့ကောင်",
        "လိမ်ဖုတ်", "ကောက်ကျစ်တဲ့ကောင်", "ကလေကချေ"
    ]
}

# English Lexicon for Fast Tier 1 Matching
ENGLISH_LEXICON = {
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

# Compile Fast Aho-Corasick or Regex Matchers
def _compile_patterns(lexicon_dict: Dict[str, List[str]]) -> Dict[str, re.Pattern]:
    compiled = {}
    for category, words in lexicon_dict.items():
        # Escape special regex characters in words
        escaped_words = [re.escape(w) for w in sorted(words, key=len, reverse=True)]
        # Word boundary or standalone match
        pattern_str = r'(' + '|'.join(escaped_words) + r')'
        compiled[category] = re.compile(pattern_str, re.IGNORECASE)
    return compiled

MM_PATTERNS = _compile_patterns(MYANMAR_LEXICON)
EN_PATTERNS = _compile_patterns(ENGLISH_LEXICON)


def fast_lexicon_check(text: str, language: str) -> Optional[Tuple[bool, float, str, str, str]]:
    """
    Tier 1 Ultra-fast Lexicon Filter.
    Returns:
    (is_harmful, confidence_score, category, matched_keyword, reason) or None if no direct match.
    """
    if not text:
        return None
    
    # Check Myanmar patterns if language is 'my' or 'mixed'
    if language in ('my', 'mixed'):
        for cat, pattern in MM_PATTERNS.items():
            match = pattern.search(text)
            if match:
                matched_word = match.group(0)
                # Hate speech & Profanity have higher baseline severity
                score = 0.95 if cat in ('hate_speech', 'profanity') else 0.85
                category_labels = {
                    "hate_speech": "Hate Speech (အမုန်းစကား)",
                    "cyberbullying": "Cyberbullying (အနိုင်ကျင့်စော်ကားမှု)",
                    "profanity": "Profanity / Toxic (ဆဲဆိုရိုင်းစိုင်းမှု)",
                    "insult": "Insult (စော်ကားနှိမ်ချမှု)"
                }
                return (
                    True,
                    score,
                    cat,
                    matched_word,
                    f"Detected harmful keyword '{matched_word}' [{category_labels.get(cat, cat)}]"
                )

    # Check English patterns if language is 'en' or 'mixed'
    if language in ('en', 'mixed'):
        for cat, pattern in EN_PATTERNS.items():
            # For English, search with boundary or substring
            match = pattern.search(text)
            if match:
                matched_word = match.group(0)
                score = 0.96 if cat in ('hate_speech', 'profanity') else 0.88
                category_labels = {
                    "hate_speech": "Hate Speech",
                    "cyberbullying": "Cyberbullying / Harassment",
                    "profanity": "Profanity / Toxicity",
                    "insult": "Insult / Derogatory"
                }
                return (
                    True,
                    score,
                    cat,
                    matched_word,
                    f"Detected harmful keyword '{matched_word}' [{category_labels.get(cat, cat)}]"
                )
    
    return None
