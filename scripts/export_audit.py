"""Draw a blind sample of answers for a human to label, to check the LLM judge.

Writes two files:
  results/audit_blind.csv  prompt + answer + empty human_label column (the judge's label is hidden)
  results/audit_key.csv    uid -> judge label (do not open it before finishing the labels)

The sample is stratified: equal numbers from base/tuned x harmful/benign.
    python scripts/export_audit.py --n 60
"""
import argparse
import csv
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import ROOT, read_jsonl  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=60)
ap.add_argument("--seed", type=int, default=20260928)
args = ap.parse_args()

res = ROOT / "results"
responses = {}
for tag in ("base", "tuned"):
    for r in read_jsonl(res / f"responses_{tag}.jsonl"):
        responses[(tag, r["set"], r["id"])] = r
judged = {}
for tag in ("base", "tuned"):
    for j in read_jsonl(res / f"judged_{tag}.jsonl"):
        judged[(j["model_tag"], j["set"], j["id"])] = j["label"]

rng = random.Random(args.seed)
strata = [(t, s) for t in ("base", "tuned") for s in ("harmful", "benign")]
per = args.n // len(strata)
sample = []
for t, s in strata:
    keys = sorted(k for k in judged if k[0] == t and k[1] == s)
    sample += rng.sample(keys, min(per, len(keys)))
rng.shuffle(sample)  # hide which model each answer came from

with open(res / "audit_blind.csv", "w", newline="", encoding="utf-8") as fb, \
     open(res / "audit_key.csv", "w", newline="", encoding="utf-8") as fk:
    wb, wk = csv.writer(fb), csv.writer(fk)
    wb.writerow(["uid", "prompt", "response", "human_label"])
    wk.writerow(["uid", "model_tag", "set", "id", "judge_label"])
    for i, k in enumerate(sample, 1):
        uid = f"A{i:03d}"
        r = responses[k]
        wb.writerow([uid, r["prompt"], r["response"], ""])
        wk.writerow([uid, k[0], k[1], k[2], judged[k]])

print(f"{len(sample)} items -> results/audit_blind.csv")
print("Fill human_label with REFUSAL, COMPLIANCE or PARTIAL (same definitions as the judge rubric).")
