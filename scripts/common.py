"""Shared helpers: JSONL I/O, hashing, and the list of files frozen by pre-registration."""
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOCK_PATH = ROOT / "prereg.lock"

# Files that must not change after scripts/freeze.py has run.
FROZEN_FILES = [
    "config/gates.yaml",
    "config/train.yaml",
    "data/eval/safety_harmful.jsonl",
    "data/eval/overrefusal_benign.jsonl",
    "data/train/safety_sft.jsonl",
]

LABELS = ("REFUSAL", "COMPLIANCE", "PARTIAL")


def read_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise SystemExit(f"{path}:{n}: invalid JSON ({e})")
    return rows


def write_jsonl(path, rows):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_lock():
    """Return (ok, problems). ok is False if the lock is missing or any frozen file changed."""
    if not LOCK_PATH.exists():
        return False, ["prereg.lock not found: run scripts/freeze.py before evaluating"]
    lock = json.loads(LOCK_PATH.read_text())
    problems = []
    for rel, digest in lock["files"].items():
        p = ROOT / rel
        if not p.exists():
            problems.append(f"{rel}: missing")
        elif sha256_file(p) != digest:
            problems.append(f"{rel}: changed since freeze")
    return not problems, problems
