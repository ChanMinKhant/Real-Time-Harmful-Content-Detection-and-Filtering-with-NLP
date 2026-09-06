"""
Bilingual Training Dataset for Harmful Content Classification (EN & MM).

Structure:
1. SEED_CORPUS - hand-curated bilingual seed samples (text, label, category, lang)
2. build_dataset(seed_multiplier) - deterministic augmentation expanding seeds
   into a balanced training set (neutral-phrase padding, particle noise,
   punctuation noise).

Labels are binary: 1 = harmful, 0 = safe. Category is kept for analysis only.
"""

import random
from typing import List, Tuple

Sample = Tuple[str, int, str, str]

# ---------------------------------------------------------------------------
# Seed corpus
# ---------------------------------------------------------------------------
SEED_CORPUS: List[Sample] = [
    # --- Safe English ---
    ("Hello everyone! Have a wonderful day!", 0, "safe", "en"),
    ("Great job on this project, keep it up!", 0, "safe", "en"),
    ("What time does the class start tomorrow?", 0, "safe", "en"),
    ("Thank you so much for your help and support.", 0, "safe", "en"),
    ("This tutorial is very helpful and well explained.", 0, "safe", "en"),
    ("I really like this music video and the melody.", 0, "safe", "en"),
    ("Congratulations on your graduation and new job!", 0, "safe", "en"),
    ("Let us know if you need any further assistance.", 0, "safe", "en"),
    ("Good morning teachers and classmates!", 0, "safe", "en"),
    ("Interesting research paper on natural language processing.", 0, "safe", "en"),
    ("I hope you have a pleasant and relaxing weekend.", 0, "safe", "en"),
    ("The weather today is really nice and sunny.", 0, "safe", "en"),
    ("Can someone recommend a good book to read?", 0, "safe", "en"),
    ("Thank you for sharing your knowledge with us.", 0, "safe", "en"),
    ("Charles Dickens wrote many classic novels.", 0, "safe", "en"),
    ("The closer we look, the more details we find.", 0, "safe", "en"),
    ("This documentary about ocean life is fascinating.", 0, "safe", "en"),
    ("Does anyone know how to fix this python error?", 0, "safe", "en"),
    ("My grandmother makes the best noodles in town.", 0, "safe", "en"),
    ("The meeting was moved to three o'clock.", 0, "safe", "en"),
    ("I passed my driving test on the first try!", 0, "safe", "en"),
    ("This coffee shop has free wifi and great pastries.", 0, "safe", "en"),
    ("Could you share the slides after the seminar?", 0, "safe", "en"),
    ("Our team won the football match yesterday evening.", 0, "safe", "en"),
    ("Reading before bed helps me sleep better.", 0, "safe", "en"),
    ("The new museum exhibit opens next Friday.", 0, "safe", "en"),
    ("I am learning to cook Burmese curry recipes.", 0, "safe", "en"),
    ("Volunteering at the shelter was a rewarding experience.", 0, "safe", "en"),
    ("The train to Mandalay leaves early in the morning.", 0, "safe", "en"),
    ("Please review my pull request when you have time.", 0, "safe", "en"),

    # --- Toxic English ---
    ("You are an ugly stupid loser nobody cares about.", 1, "cyberbullying", "en"),
    ("Shut up you idiot, your project is complete garbage and nobody cares.", 1, "insult", "en"),
    ("Go die you pathetic piece of trash.", 1, "cyberbullying", "en"),
    ("I hate all immigrants, they should get out of our country.", 1, "hate_speech", "en"),
    ("What the fuck is wrong with you dumbass bitch.", 1, "profanity", "en"),
    ("You deserve to be bullied for being so fat and weird.", 1, "cyberbullying", "en"),
    ("Fucking bastard get out of here.", 1, "profanity", "en"),
    ("You brainless clown, you know nothing about AI.", 1, "insult", "en"),
    ("Nobody loves you, you are a complete failure.", 1, "cyberbullying", "en"),
    ("Kill yourself, you worthless piece of shit.", 1, "cyberbullying", "en"),
    ("All of you people are subhuman and should disappear.", 1, "hate_speech", "en"),
    ("You are so disgusting, kill yourself already.", 1, "cyberbullying", "en"),
    ("Stupid moron, you failed again didn't you?", 1, "insult", "en"),
    ("Your opinion is garbage and so are you, asshole.", 1, "profanity", "en"),
    ("Fat ugly pig, stop posting selfies.", 1, "cyberbullying", "en"),
    ("We don't want your kind here, filthy immigrant.", 1, "hate_speech", "en"),
    ("Shut the hell up you dumbass.", 1, "profanity", "en"),
    ("Everyone laughs at you behind your back, pathetic loser.", 1, "cyberbullying", "en"),
    ("You are a waste of oxygen.", 1, "cyberbullying", "en"),
    ("Go back to your country, terrorist.", 1, "hate_speech", "en"),
    ("What a brainless imbecile, can't even do basic math.", 1, "insult", "en"),
    ("Bitch, nobody asked for your stupid comment.", 1, "profanity", "en"),
    ("Jump off a cliff, freak.", 1, "cyberbullying", "en"),
    ("You scumbag, lying piece of trash.", 1, "insult", "en"),
    ("Ugly freak, nobody will ever love you.", 1, "cyberbullying", "en"),

    # --- Safe Myanmar ---
    ("အားလုံးပဲ မင်္ဂလာပါခင်ဗျာ။ ကောင်းသောနေ့လေးဖြစ်ပါစေ။", 0, "safe", "my"),
    ("ဒီ Post လေးက အရမ်းဗဟုသုတရပါတယ် ကျေးဇူးတင်ပါတယ်။", 0, "safe", "my"),
    ("စာမေးပွဲအတွက် အားလုံး ကြိုးစားကြပါ အောင်မြင်ပါစေ။", 0, "safe", "my"),
    ("မင်္ဂလာမနက်ခင်းပါ ဆရာတို့ သူငယ်ချင်းတို့ရေ။", 0, "safe", "my"),
    ("ဒီ project လေး တော်တော်ကောင်းတယ် ဆက်ကြိုးစားပါဗျာ။", 0, "safe", "my"),
    ("သီချင်းလေးက အရမ်းနားထောင်လို့ကောင်းတယ် ကြိုက်တယ်။", 0, "safe", "my"),
    ("အကြံပေးချက်အတွက် အထူးပင် ကျေးဇူးတင်ရှိပါသည်။", 0, "safe", "my"),
    ("မုန့်သွားစားကြမလား သူငယ်ချင်းတို့။", 0, "safe", "my"),
    ("ကျောင်းပိတ်ရက် ဘယ်သွားကြမလဲဗျ။", 0, "safe", "my"),
    ("ကျန်းမာချမ်းသာကြပါစေလို့ ဆုတောင်းမေတ္တာပို့သအပ်ပါတယ်။", 0, "safe", "my"),
    ("စာအုပ်ကောင်းလေးတွေ ညွှန်းပေးကြပါဦးခင်ဗျာ။", 0, "safe", "my"),
    ("ဒီဇာတ်ကားလေး ကြည့်ဖို့ အကြံပြုချင်ပါတယ်။", 0, "safe", "my"),
    ("မနက်ဖြန် ဈေးသွားကြမလား သူငယ်ချင်းရေ။", 0, "safe", "my"),
    ("ဒီဟင်းလျာလေး ချက်နည်းကို ဝေမျှပေးပါဦး။", 0, "safe", "my"),
    ("မိုးရွာလို့ ခရီးမသွားနိုင်တော့ဘူး။", 0, "safe", "my"),
    ("ရုပ်ရှင်ရုံက လူအရမ်းများနေတယ်။", 0, "safe", "my"),
    ("ကျွန်တော့်ရဲ့ မိသားစု အားလုံး သန်မာပါစေ။", 0, "safe", "my"),
    ("ဒီဓာတ်ပုံလေးက လှလှလေးပဲဘဲ။", 0, "safe", "my"),
    ("ဘာသာစကားသင်တန်းလေး တက်ချင်တယ်။", 0, "safe", "my"),
    ("ညနေပိုင်း လေထီးကြီးပျံသနားကောင်းတယ်။", 0, "safe", "my"),
    ("ကျွန်မ စာရွက်စာတမ်းလေး ရေးနေပါတယ်။", 0, "safe", "my"),
    ("ဒီနေ့ ရာသီဥတု အေးအေးလေးရှိတယ်။", 0, "safe", "my"),
    ("သူငယ်ချင်းတွေ စည်းလုံးကြပါစို့။", 0, "safe", "my"),
    ("အိမ်ပြန်တဲ့အခါ သတိထားပါနော်။", 0, "safe", "my"),
    ("ဒီသီပုံပြင်လေး နားထောင်ရတာ သဘာဝကျတယ်။", 0, "safe", "my"),

    # --- Toxic Myanmar ---
    ("ဒီကောင်က တော်တော်ရိုင်းတာပဲ ခွေးလိုကောင်။", 1, "profanity", "my"),
    ("မင်းလို အသုံးမကျတဲ့ ငတုံးက ဘာသိမှာလဲ သွားသေလိုက်။", 1, "cyberbullying", "my"),
    ("ရုပ်ကိုက ရွံစရာကောင်းလိုက်တာ အပေါစားမ။", 1, "cyberbullying", "my"),
    ("ဒီလူမျိုးတွေက တိုင်းပြည်ဖျက်တဲ့ ခွေးကုလားတွေပဲ မျိုးမစစ်တွေ။", 1, "hate_speech", "my"),
    ("စောက်ချိုးမပြေတဲ့ကောင် မအေလိုးသား။", 1, "profanity", "my"),
    ("အဆင့်မရှိတဲ့ အောက်တန်းစားတွေ ဘာမှမသိဘဲ လာပြောနေတယ်။", 1, "insult", "my"),
    ("မျက်နှာပြောင်ပြီး လာလိမ်နေတဲ့ သူခိုးကောင်။", 1, "insult", "my"),
    ("အဆီပုတ်ကြီးနဲ့ ဝက်လိုကောင် ရွံဖို့ကောင်းလိုက်တာ။", 1, "cyberbullying", "my"),
    ("မင်းလိုးမ၊ မင်းမျက်နှာက ရွံစရာကောင်းတယ်။", 1, "profanity", "my"),
    ("တိုင်းတစ်ပါးသားခွေးတွေ ဘယ်သွားကြတော့မလဲ။", 1, "hate_speech", "my"),
    ("မင်းအသက်ရှင်နေတာအပိုပဲ သွားသေလိုက်ပါလား။", 1, "cyberbullying", "my"),
    ("ခွေးသား မင်းစကား မျက်နှာမွဲတယ်။", 1, "profanity", "my"),
    ("ငနပိကောင် လိမ်ညာတဲ့ကောင်များ။", 1, "insult", "my"),
    ("ဖက်တီးကြီး မျက်နှာအရုပ်ဆိုးတဲ့ကောင်။", 1, "cyberbullying", "my"),
    ("စောက်ရမ်းကြီးတဲ့ ခွေးမသား ဘာပြောနေတာလဲ။", 1, "profanity", "my"),
    ("လူမျိုးတုံးဖို့ ကြိုးပမ်းနေတဲ့ ဘာသာဖျက်တွေ။", 1, "hate_speech", "my"),
    ("အရူးကောင်လေး ရူးနေလား မင်း။", 1, "insult", "my"),
    ("မအေဘေးကောင် စောက်ရမ်းကြီးလို့။", 1, "profanity", "my"),
    ("မင်းတို့လို အသုံးမကျတဲ့ဟာတွေ တိုးဝှက်မနေနဲ့။", 1, "cyberbullying", "my"),
    ("ကုလားဆိုးတွေ ကျွန်တော်တို့နိုင်ငံက ထွက်သွားကြစေ။", 1, "hate_speech", "my"),
    ("မရှက်ဘူးလား မျက်နှာပြောင် အပေါစား။", 1, "insult", "my"),
    ("ဝက်မလိုကောင် စားတတ်တဲ့အဆီပုတ်။", 1, "cyberbullying", "my"),
    ("လီးပဲ မင်းသိတဲ့အတိုင်း ခွေးလိုကောင်။", 1, "profanity", "my"),
    ("တောသားလေးတွေ ဘာမှမသိဘဲ ပြောနေကြတာ။", 1, "insult", "my"),
]

# ---------------------------------------------------------------------------
# Deterministic augmentation
# ---------------------------------------------------------------------------
_EN_NEUTRAL_PREFIX = ["honestly,", "imo,", "tbh,", "fr,", "well,", "look,", "dude,", ""]
_EN_NEUTRAL_SUFFIX = ["lol", "lmao", "smh", "bro", "man", "...", "!!", "?!", ""]

_MM_TOXIC_PREFIX = ["မင်း", "သူ", "ဒီကောင်", "ချ", "ကွာ", ""]
_MM_TOXIC_SUFFIX = ["ကွာ", "လေ", "ပဲ", "တာပဲ", "ဟုတ်တယ်", ""]
_MM_SAFE_PREFIX = ["သူငယ်ချင်းတို့", "အားလုံး", "ကျွန်တော်", "", ""]
_MM_SAFE_SUFFIX = ["နော်", "ဗျာ", "ပါ", "ခင်ဗျာ", ""]


def _augment_en(text: str, label: int, rng: random.Random) -> str:
    parts = [text]
    prefix = rng.choice(_EN_NEUTRAL_PREFIX)
    suffix = rng.choice(_EN_NEUTRAL_SUFFIX)
    if prefix:
        parts.insert(0, prefix)
    if suffix:
        parts.append(suffix)
    out = " ".join(p for p in parts if p)
    if rng.random() < 0.3 and label == 1:
        # mild obfuscation noise so ML learns evasion-resistant features
        out = out.replace("u", "u", 1)
    return out


def _augment_mm(text: str, label: int, rng: random.Random) -> str:
    pool = _MM_TOXIC_PREFIX if label == 1 else _MM_SAFE_PREFIX
    sfx_pool = _MM_TOXIC_SUFFIX if label == 1 else _MM_SAFE_SUFFIX
    prefix = rng.choice(pool)
    suffix = rng.choice(sfx_pool)
    out = text
    if prefix and not out.startswith(prefix):
        out = f"{prefix} {out}"
    if suffix and rng.random() < 0.6:
        out = f"{out}{suffix}"
    return out


def build_dataset(seed: int = 42) -> List[Sample]:
    """Expands the seed corpus ~8x with deterministic bilingual noise."""
    rng = random.Random(seed)
    dataset: List[Sample] = []
    for text, label, category, lang in SEED_CORPUS:
        dataset.append((text, label, category, lang))
        augment = _augment_mm if lang == "my" else _augment_en
        seen = {text}
        copies = 0
        while copies < 7:
            variant = augment(text, label, rng)
            if variant in seen:
                continue
            seen.add(variant)
            dataset.append((variant, label, category, lang))
            copies += 1
    rng.shuffle(dataset)
    return dataset


def texts_and_labels(dataset: List[Sample]) -> Tuple[List[str], List[int]]:
    return [d[0] for d in dataset], [d[1] for d in dataset]


if __name__ == "__main__":
    ds = build_dataset()
    harmful = sum(1 for d in ds if d[1] == 1)
    mm = sum(1 for d in ds if d[3] == "my")
    print(f"Total samples : {len(ds)}")
    print(f"Harmful       : {harmful} | Safe: {len(ds) - harmful}")
    print(f"Myanmar       : {mm} | English: {len(ds) - mm}")
