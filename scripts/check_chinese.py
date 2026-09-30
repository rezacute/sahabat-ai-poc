"""Build-time guard: fail if any data file contains CJK / fullwidth / non-Latin
characters that Indonesian, Javanese and Sundanese do not use.

Indonesian, Javanese and Sundanese are all written in the Latin alphabet (with
optional diacritics). Any character outside the Latin blocks is a leakage.

Allowed Unicode blocks:
  Basic Latin (U+0020 - U+007F)
  Latin-1 Supplement (U+0080 - U+00FF)        — punctuation like ¡, ©
  Latin Extended-A (U+0100 - U+017F)          — ā, ē, etc.
  Latin Extended-B (U+0180 - U+024F)
  Latin Extended Additional (U+1E00 - U+1EFF) — diacritics
  General Punctuation (U+2000 - U+206F)        — em-dash, curly quotes
  Currency Symbols (U+20A0 - U+20CF)          — Rp, etc.
  Letterlike Symbols (U+2100 - U+214F)        — ™, etc.
  Latin ligatures (U+FB00 - U+FB06)            — fi, fl

Disallowed:
  CJK (U+3000-303F, U+3400-4DBF, U+4E00-9FFF, U+20000-2A6DF, U+2A700-2EBEF)
  Fullwidth ASCII (U+FF00 - U+FFEF)
  Hiragana, Katakana, Hangul, Arabic, Cyrillic, Greek, Devanagari, Thai

Why not a regex with \\uXXXX escapes?
  Python re silently mis-parses \x4E inside a character class (treats as literal 'N'),
  which means re.compile(r'[\u4E00-\u9FFF]') does NOT match the intended range.
  Use ord() range comparisons instead.

Usage:
  python scripts/check_chinese.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (lo, hi) inclusive Unicode code-point ranges
NON_LATIN_RANGES = [
    (0x3000, 0x303F),    # CJK punctuation
    (0x3400, 0x4DBF),    # CJK Ext A
    (0x4E00, 0x9FFF),    # CJK Unified Ideographs
    (0x20000, 0x2A6DF),  # CJK Ext B
    (0x2A700, 0x2EBEF),  # CJK Ext C-F
    (0xFF00, 0xFFEF),    # Fullwidth ASCII
    (0x3040, 0x309F),    # Hiragana
    (0x30A0, 0x30FF),    # Katakana
    (0xAC00, 0xD7AF),    # Hangul
    (0x0600, 0x06FF),    # Arabic
    (0x0400, 0x04FF),    # Cyrillic
    (0x0370, 0x03FF),    # Greek
    (0x0900, 0x097F),    # Devanagari
    (0x0E00, 0x0E7F),    # Thai
]


def is_blocked_char(c):
    cp = ord(c)
    return any(lo <= cp <= hi for lo, hi in NON_LATIN_RANGES)


def has_emoji(text):
    """Detect any emoji code-point in text."""
    for c in text:
        cp = ord(c)
        if (0x1F300 <= cp <= 0x1F9FF) or (0x2600 <= cp <= 0x26FF) or (0x1F600 <= cp <= 0x1F64F):
            return c
    return None


def text_for_check(d):
    """Flatten a jsonl record into a string to scan."""
    return json.dumps(d, ensure_ascii=False)


def main():
    targets = [
        ROOT / "data/eval/safety_harmful.jsonl",
        ROOT / "data/eval/overrefusal_benign.jsonl",
        ROOT / "data/train/safety_sft.jsonl",
    ]
    hits = []
    for path in targets:
        if not path.exists():
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"{path}:{n}: invalid JSON ({e})", file=sys.stderr)
                return 1
            text = text_for_check(d)
            for c in text:
                if is_blocked_char(c):
                    hits.append((str(path.relative_to(ROOT)), n, "non-Latin",
                                 hex(ord(c)), c))
                    break
            e = has_emoji(text)
            if e:
                hits.append((str(path.relative_to(ROOT)), n, "emoji",
                             hex(ord(e)), e))
    if hits:
        print(f"FAIL: {len(hits)} CJK / fullwidth / emoji leakage(s) found", file=sys.stderr)
        for h in hits:
            print(f"  {h[0]}:{h[1]} {h[2]} U+{h[3][2:].upper()} {h[4]!r}", file=sys.stderr)
        return 1
    print("OK: no CJK / fullwidth / emoji leakage in data files")
    return 0


if __name__ == "__main__":
    sys.exit(main())