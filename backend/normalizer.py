"""
Text Normalization and Preprocessing Module for English & Myanmar (Burmese).
Academic Concepts implemented:
1. Unicode Canonical Ordering & NFC Decomposition
2. Myanmar Syllable Break Segmentation (Rule-based Regex)
3. Subword & Lexical Cleaning & Leetspeak Deobfuscation
"""

import json
import os
import re
import unicodedata
from pathlib import Path
from typing import List, Tuple

# Myanmar Unicode Range: 0x1000 - 0x109F, extended ranges \uAA60-\uAA7F, \uA9E0-\uA9FF
MYANMAR_REGEX = re.compile(r'[\u1000-\u109F\uAA60-\uAA7F\uA9E0-\uA9FF]')

# Myanmar Syllable Breaking Regular Expression
# Consonants / Independent vowels: \u1000-\u1021, \u1023-\u102A, \u103F, \u104E
# Stacked: [\u103A]?\u1039[\u1000-\u1021] (subscript consonant, incl. kinzi form: ...င်္ဂ...)
# Medials: \u103B-\u103E
# Vowels: \u102B-\u1035, \u1031, \u1032
# Killers/Tones: optional coda consonant+asat (closed syllable, e.g. လိုက်),
# then bare asat (only when NOT opening a stack), then \u1036-\u1038
MYANMAR_SYLLABLE_PATTERN = re.compile(
    r'(?<![\u103A\u1039])'
    r'('
    r'[\u1000-\u1021\u1023-\u102A\u103F\u104E]'
    r'(?:[\u103A]?[\u1039][\u1000-\u1021])*'
    r'(?:[\u103B-\u103E])*'
    r'(?:[\u102B-\u1035\u1031\u1032])*'
    r'(?:[\u1000-\u1021\u1023-\u102A\u103F]\u103A(?!\u1039))?'
    r'(?:\u103A(?!\u1039))*'
    r'[\u1036\u1037\u1038]*'
    r')'
)

# Load leetspeak mapping from shared rules if available, else default fallback
DEFAULT_LEET_MAP = {
    '0': 'o', '1': 'i', '!': 'i', '|': 'l', '3': 'e', '4': 'a',
    '5': 's', '$': 's', '7': 't', '+': 't', '8': 'b', '9': 'g', '<': 'c',
}


def _load_leet_map() -> dict:
    shared_rules = Path(__file__).resolve().parent.parent / "shared" / "rules.json"
    if shared_rules.exists():
        try:
            with open(shared_rules, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("leetspeak", {}).get("char_map", DEFAULT_LEET_MAP)
        except Exception:
            pass
    return DEFAULT_LEET_MAP


LEET_MAP_DICT = _load_leet_map()
LEET_TRANS = str.maketrans(LEET_MAP_DICT)
LEET_RE = re.compile(r'(?<=[A-Za-z])[0-9!@#$+|<$](?=[A-Za-z])')


def normalize_myanmar_unicode(text: str) -> str:
    """
    Normalizes Myanmar text to standard Unicode 5.1+ encoding.
    Fixes reordered vowels and duplicated diacritics.
    """
    if not text:
        return ""
    
    # Standard Unicode NFC normalization
    text = unicodedata.normalize('NFC', text)
    
    # Fix zero-width spaces / non-breaking spaces
    text = text.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '').replace('\ufeff', '')
    
    # Fix duplicate tone marks / duplicate asat
    text = re.sub(r'([\u103A])+', r'\1', text)
    text = re.sub(r'([\u1037])+', r'\1', text)
    text = re.sub(r'([\u1038])+', r'\1', text)
    
    # Normalize common typing order typos (e.g. ေ preceding consonant -> consonant + ေ)
    text = re.sub(r'(\u1031)([\u1000-\u1021])', r'\2\1', text)
    
    return text.strip()


def segment_myanmar_syllables(text: str) -> List[str]:
    """
    Segments continuous Myanmar script into discrete syllables.
    Example: 'မင်္ဂလာပါ' -> ['မ', 'င်္ဂ', 'လာ', 'ပါ']
    """
    if not text:
        return []
    normalized = normalize_myanmar_unicode(text)
    syllables = MYANMAR_SYLLABLE_PATTERN.findall(normalized)
    if not syllables:
        return [c for c in normalized if not c.isspace()]
    return [s for s in syllables if s.strip()]


def deobfuscate_english(text: str) -> str:
    """
    Reverses common character-substitution evasion (sh1t -> shit, 5t@r -> star).
    Only substitutes characters embedded between letters to leave ordinary numbers intact.
    """
    if not text:
        return ""
    return LEET_RE.sub(lambda m: m.group(0).translate(LEET_TRANS), text)


def clean_english_text(text: str) -> str:
    """
    Preprocesses and cleans English text:
    - Lowercase
    - Deobfuscate leetspeak evasions
    - Normalize whitespace
    - Squeeze excessive repeated characters (e.g. sooooo -> soo)
    """
    if not text:
        return ""
    text = text.lower().strip()
    text = deobfuscate_english(text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'(.)\1{2,}', r'\1\1', text)
    return text


def detect_language(text: str) -> str:
    """
    Detects language script of given text:
    - 'my': Myanmar (Burmese)
    - 'en': English
    - 'mixed': Contains both significantly
    """
    if not text:
        return "en"
    
    has_myanmar = bool(MYANMAR_REGEX.search(text))
    has_english = bool(re.search(r'[a-zA-Z]', text))
    
    if has_myanmar and has_english:
        return "mixed"
    elif has_myanmar:
        return "my"
    return "en"


def preprocess_text(text: str) -> Tuple[str, str, List[str]]:
    """
    Full text preprocessing pipeline.
    Returns:
    - cleaned_text: Normalized string
    - language: 'en', 'my', or 'mixed'
    - tokens: List of word or syllable tokens
    """
    if not text:
        return "", "en", []
    
    lang = detect_language(text)
    
    if lang in ('my', 'mixed'):
        cleaned = normalize_myanmar_unicode(text)
        syllables = segment_myanmar_syllables(cleaned)
        return cleaned, lang, syllables
    else:
        cleaned = clean_english_text(text)
        tokens = cleaned.split()
        return cleaned, lang, tokens
