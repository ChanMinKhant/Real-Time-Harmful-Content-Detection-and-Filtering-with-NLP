#!/usr/bin/env python3
"""
Lexicon Synchronization Utility.
Reads `shared/rules.json` as the Single Source of Truth and validates / exports
to `extension/rules.js` for the Chrome Extension.
"""

import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES_PATH = os.path.join(PROJECT_ROOT, "shared", "rules.json")
EXTENSION_RULES_PATH = os.path.join(PROJECT_ROOT, "extension", "rules.js")


def load_rules():
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_extension_rules(rules: dict) -> str:
    js_content = f"""/**
 * AUTO-GENERATED from shared/rules.json via scripts/sync_lexicon.py
 * Single Source of Truth for Bilingual Toxic Lexicons and Pattern Matchers.
 */

const BLUR_RULES = Object.freeze({json.dumps(rules, indent=2, ensure_ascii=False)});

if (typeof module !== "undefined" && module.exports) {{
  module.exports = BLUR_RULES;
}}
"""
    return js_content


def main():
    if not os.path.exists(RULES_PATH):
        print(f"❌ Error: {RULES_PATH} not found.")
        sys.exit(1)

    rules = load_rules()
    categories = rules.get("categories", {})
    mm_words = sum(len(v) for v in rules.get("myanmar_lexicon", {}).values())
    en_words = sum(len(v) for v in rules.get("english_lexicon", {}).values())

    print(f"📖 Loaded rules v{rules.get('version')}:")
    print(f"   - Categories       : {len(categories)} ({', '.join(categories.keys())})")
    print(f"   - Myanmar Keywords : {mm_words}")
    print(f"   - English Keywords : {en_words}")

    if "--check" in sys.argv:
        if not os.path.exists(EXTENSION_RULES_PATH):
            print(f"❌ Check failed: {EXTENSION_RULES_PATH} does not exist.")
            sys.exit(1)
        print("✅ Rules are valid.")
        return

    # Write to extension
    js_content = generate_extension_rules(rules)
    with open(EXTENSION_RULES_PATH, "w", encoding="utf-8") as f:
        f.write(js_content)
    print(f"✅ Successfully synchronized rules to {EXTENSION_RULES_PATH}")


if __name__ == "__main__":
    main()
