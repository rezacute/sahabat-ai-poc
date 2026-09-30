"""Build-time guard for non-Latin language leakage in id/jv/su data.

Indonesian, Javanese and Sundanese all use the Latin alphabet. The script-based
check (this file) is the primary guard: any character outside the Latin blocks
that id/jv/su legitimately use indicates leakage.

A secondary, opt-in langdetect check is provided for longer texts where it is
more reliable, but it is NOT enabled by default because langdetect confuses
short Javanese and Sundanese prompts with Tagalog / Indonesian, causing false
positives on legitimate jv/su data.

Usage:
  python scripts/check_languages.py               # script-only (primary)
  python scripts/check_languages.py --with-langdetect   # adds langdetect
                                                # for long texts (>= 100 chars)
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

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


def is_emoji(c):
    cp = ord(c)
    return ((0x1F300 <= cp <= 0x1F9FF) or (0x2600 <= cp <= 0x26FF)
            or (0x1F600 <= cp <= 0x1F64F))


def check_script(path, primary=True):
    """Walk every record; flag any non-Latin character."""
    hits = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        text = json.dumps(d, ensure_ascii=False)
        for c in text:
            if is_blocked_char(c):
                hits.append((path.name, n, "non-Latin", hex(ord(c)), c))
                break
            if is_emoji(c):
                hits.append((path.name, n, "emoji", hex(ord(c)), c))
                break
    return hits


def check_langdetect(path):
    """Informational only: use langdetect to flag long texts in non-target langs."""
    try:
        from langdetect import detect, DetectorFactory
        DetectorFactory.seed = 0
    except ImportError:
        print("INFO: langdetect not installed; skipping --with-langdetect",
              file=sys.stderr)
        return []
    allowed = {"id", "jv", "su"}  # iso639-1 codes
    # langdetect does not have 'jv' or 'su' reliably; map them by hand
    known = {"id": "id", "jv": "jv", "su": "su"}
    hits = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        d = json.loads(line)
        text = json.dumps(d, ensure_ascii=False)
        if len(text) < 100:
            continue
        try:
            lang = detect(text)
        except Exception:
            continue
        if lang in {"id", "ms"}:  # ms often confused for jv
            continue
        hits.append((path.name, n, f"langdetect={lang}", "", text[:80]))
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-langdetect", action="store_true",
                    help="additionally run langdetect on long texts (informational)")
    args = ap.parse_args()

    targets = [
        ROOT / "data/eval/safety_harmful.jsonl",
        ROOT / "data/eval/overrefusal_benign.jsonl",
        ROOT / "data/train/safety_sft.jsonl",
    ]
    primary_hits = []
    for path in targets:
        if path.exists():
            primary_hits.extend(check_script(path))

    if primary_hits:
        print(f"FAIL (script check): {len(primary_hits)} non-Latin / emoji hit(s)",
              file=sys.stderr)
        for h in primary_hits:
            print(f"  {h[0]}:{h[1]} {h[2]} U+{h[3][2:].upper()} {h[4]!r}", file=sys.stderr)
        return 1

    if args.with_langdetect:
        secondary_hits = []
        for path in targets:
            if path.exists():
                secondary_hits.extend(check_langdetect(path))
        if secondary_hits:
            print(f"WARN (langdetect, informational): {len(secondary_hits)} long-text surprise(s)")
            for h in secondary_hits:
                print(f"  {h[0]}:{h[1]} {h[2]}: {h[4]!r}")
            print("(this is informational — short jv/su prompts are noisy for langdetect)")
        else:
            print("OK (script + langdetect): no language leakage")
    else:
        print("OK (script check): no non-Latin / emoji leakage in data files")
        print("(use --with-langdetect to additionally scan long texts)")
    return 0


if __name__ == "__main__":
    sys.exit(main())