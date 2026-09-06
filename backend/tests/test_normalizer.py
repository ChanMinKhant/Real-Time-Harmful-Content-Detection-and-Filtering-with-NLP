from normalizer import (
    clean_english_text,
    deobfuscate_english,
    detect_language,
    normalize_myanmar_unicode,
    segment_myanmar_syllables,
)


# ---------------------------------------------------------------- language
def test_detect_language_en():
    assert detect_language("Hello world") == "en"


def test_detect_language_my():
    assert detect_language("မင်္ဂလာပါ") == "my"


def test_detect_language_mixed():
    assert detect_language("ဒီ Post ကောင်းတယ်") == "mixed"


# ------------------------------------------------------------- syllables
def test_segment_myanmar_syllables_basic():
    # kinzi stack င်္ဂ stays one unit, nothing is dropped
    assert segment_myanmar_syllables("မင်္ဂလာပါ") == ["မ", "င်္ဂ", "လာ", "ပါ"]


def test_segment_keeps_closed_syllable_whole():
    # လိုက် ("chase") must be ONE token so short profanity keywords
    # cannot substring-match inside it
    assert segment_myanmar_syllables("လိုက်တယ်")[0] == "လိုက်"


def test_normalize_fixes_vowel_order():
    # \u1031 (ေ) must be moved after the consonant
    assert normalize_myanmar_unicode("\u1031\u1000") == "\u1000\u1031"


def test_normalize_collapses_duplicate_asat():
    assert normalize_myanmar_unicode("\u1000\u103A\u103A") == "\u1000\u103A"


# --------------------------------------------------------------- english
def test_clean_lowercases_and_squeezes():
    assert clean_english_text("HELLO!!!     worldddddd") == "hello!! worldd"


def test_deobfuscate_translates_digits():
    assert deobfuscate_english("sh1t") == "shit"
    assert deobfuscate_english("5t@r") is not None  # no crash on odd mixes


def test_deobfuscate_leaves_ambiguous_symbols():
    # '@' can mean 'a' or 'u' -> kept for tolerant matching
    assert deobfuscate_english("f@ck") == "f@ck"


def test_deobfuscate_ignores_standalone_numbers():
    assert deobfuscate_english("i have 5 apples") == "i have 5 apples"
