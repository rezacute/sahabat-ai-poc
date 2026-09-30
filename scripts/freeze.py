"""Freeze the gates, training config and all datasets by recording their SHA-256 hashes.

Run once, after the human review of the data and before any evaluation of the tuned model.
    python scripts/freeze.py
"""
import datetime
import json
import sys

from common import FROZEN_FILES, LOCK_PATH, ROOT, sha256_file

if LOCK_PATH.exists() and "--force" not in sys.argv:
    sys.exit("prereg.lock already exists. Re-freezing is a deviation: log it in "
             "logs/DEVIATIONS.md first, then run with --force.")

files = {}
for rel in FROZEN_FILES:
    p = ROOT / rel
    if not p.exists():
        sys.exit(f"Cannot freeze: {rel} does not exist yet.")
    files[rel] = sha256_file(p)

lock = {
    "frozen_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "refrozen": "--force" in sys.argv,
    "files": files,
}
LOCK_PATH.write_text(json.dumps(lock, indent=2) + "\n")
print(f"Wrote {LOCK_PATH.name}:")
for rel, d in files.items():
    print(f"  {d[:16]}  {rel}")
