"""
Text Normalization and Preprocessing Module for English & Myanmar (Burmese).
Academic Concepts implemented:
1. Unicode Canonical Ordering & Decomposition
2. Myanmar Syllable Break Segmentation (Rule-based Regex)
3. Subword & Lexical Cleaning
"""

import re
import unicodedata
from typing import Tuple, List

# Myanmar Unicode Range: 0x1000 - 0x109F
MYANMAR_REGEX = re.compile(r'[\u1000-\u109F\uAA60-\uAA7F\uA9E0-\uA9FF]')

# Myanmar Syllable Breaking Regular Expression
# Consonants / Independent vowels: \u1000-\u1021, \u1023-\u102A, \u103F, \u104E
# Stacked: \u1039[\u1000-\u1021]
# Medials: \u103B, \u103C, \u103D, \u103E (\u103B-\u103E)
# Vowels: \u102B-\u1035, \u1031, \u1032
# Tone / Killers: \u1036, \u1037, \u1038, \u103A
MYANMAR_SYLLABLE_PATTERN = re.compile(
    r'(?<![\u103A\u1039])'
    r'('
    r'[\u1000-\u1021\u1023-\u102A\u103F\u104E]'
    r'(?:[\u1039][\u1000-\u1021])*'
    r'(?:[\u103B-\u103E])*'
    r'(?:[\u102B-\u1035\u1031\u1032])*'
    r'(?:[\u1036\u1037\u1038\u103A])*'
    r')'
)

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
    
    # Normalize common typing order typos (e.g. ေ preceding consonant)
    text = re.sub(r'(\u1031)([\u1000-\u1021])', r'\2\1', text)
    
    return text.strip()


def segment_myanmar_syllables(text: str) -> List[str]:
    """
    Segments continuous Myanmar script into discrete syllables.
    Example: 'မင်္ဂလာပါ' -> ['မင်္ဂ', 'လာ', 'ပါ']
    """
    normalized = normalize_myanmar_unicode(text)
    syllables = MYANMAR_SYLLABLE_PATTERN.findall(normalized)
    if not syllables:
        return [c for c in normalized if not c.isspace()]
    return [s for s in syllables if s.strip()]


def clean_english_text(text: str) -> str:
    """
    Preprocesses and cleans English text:
    - Lowercase
    - Remove extra whitespaces
    - Reduce character floods
    """
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'(.)\1{2,}', r'\1\1', text)
    return text


def detect_language(text: str) -> str:
    """
    Detects language of given text:
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
    Full preprocessing pipeline:
    Returns:
    - cleaned_text: Normalized string
    - language: 'en', 'my', or 'mixed'
    - tokens: List of word or syllable tokens
    """
    lang = detect_language(text)
    
    if lang in ('my', 'mixed'):
        cleaned = normalize_myanmar_unicode(text)
        syllables = segment_myanmar_syllables(cleaned)
        return cleaned, lang, syllables
    else:
        cleaned = clean_english_text(text)
        tokens = cleaned.split()
        return cleaned, lang, tokens
