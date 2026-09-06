import pytest

from lexicon_mm import fast_lexicon_check as check
from normalizer import clean_english_text


# ------------------------------------------------- false-positive regression
@pytest.mark.parametrize("text", [
    "Charles Dickens was a great writer.",
    "the closer of the ceremony",
    "what a classic movie",
    "i will thrash this out tomorrow",
    "Scrap the idea, it is fine.",
])
def test_benign_words_do_not_trigger(text):
    assert check(clean_english_text(text), "en") is None


# ------------------------------------------------------------- true positives
@pytest.mark.parametrize("raw", [
    "you are fucking bastard",
    "sh1t happens",
    "f@ck you",
    "b!tch please",
    "a$$hole",
])
def test_profanity_variants_detected(raw):
    result = check(clean_english_text(raw), "en")
    assert result is not None
    assert result[0] is True
    assert result[2] == "profanity"


def test_insult_category():
    assert check(clean_english_text("you idiot"), "en")[2] == "insult"


def test_hate_speech_category():
    assert check("he is a nigger", "en")[2] == "hate_speech"


# --------------------------------------------------------- myanmar syllables
def test_mm_keyword_inside_other_word_not_matched():
    # လိုး (profanity) must NOT fire inside လိုက် ("chase") or မလိုပဲ
    assert check("သူက ကျွန်တော့်ကို လိုက်နေတယ်", "my") is None


def test_mm_standalone_syllable_matched():
    # real lexicon entry မအေဘေး (cyberbullying) forms its own syllable tokens
    result = check("မအေဘေးကောင်", "my")
    assert result is not None and result[2] == "cyberbullying"


def test_mm_similar_innocent_word_not_matched():
    # မား (proud/firm) is a single syllable - must not trigger မအ
    assert check("ဂုဏ်သိက္ခာ မားမားရှိတယ်", "my") is None


def test_mm_profanity_phrase():
    result = check("မင်းလိုးမ", "my")
    assert result is not None and result[2] == "profanity"


def test_mm_hate_speech():
    result = check("ဒီလူမျိုးတွေက ခွေးကုလားတွေပဲ", "my")
    assert result is not None and result[2] == "hate_speech"


def test_empty_text_returns_none():
    assert check("", "en") is None
