"""Check that no evaluation prompt leaked into the training data.

Flags a pair when:
  * the normalized texts are identical, or
  * they share >= 50% of word 8-grams (long prompts), or
  * character similarity >= 0.85 (short prompts, fewer than 8 words).

Writes results/contamination.json. Fails (exit code 1) if anything is flagged.
    python scripts/contamination_check.py
"""
import difflib
import json
import re
import sys
from collections import defaultdict

from common import ROOT, read_jsonl

N = 8
NGRAM_THRESHOLD = 0.5
CHAR_THRESHOLD = 0.85


def norm(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def ngrams(words, n=N):
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def train_prompts(rows):
    out = []
    for r in rows:
        prompt = r["prompt"]
        if isinstance(prompt, list):  # conversational format
            prompt = " ".join(m["content"] for m in prompt if m.get("role") == "user")
        out.append((r.get("id", "?"), prompt))
    return out


def main():
    train = train_prompts(read_jsonl(ROOT / "data/train/safety_sft.jsonl"))
    evals = []
    for name in ("safety_harmful", "overrefusal_benign"):
        for r in read_jsonl(ROOT / f"data/eval/{name}.jsonl"):
            evals.append((f"{name}:{r['id']}", r["prompt"]))

    train_norm = [(tid, norm(t)) for tid, t in train]
    train_exact = defaultdict(list)
    index = defaultdict(set)  # 8-gram -> train indices
    for i, (tid, t) in enumerate(train_norm):
        train_exact[t].append(tid)
        for g in ngrams(t.split()):
            index[g].add(i)

    flagged = []
    for eid, e in evals:
        en = norm(e)
        words = en.split()
        if en in train_exact:
            flagged.append({"eval": eid, "train": train_exact[en], "reason": "exact"})
            continue
        if len(words) >= N:
            eg = ngrams(words)
            hits = defaultdict(int)
            for g in eg:
                for i in index.get(g, ()):
                    hits[i] += 1
            for i, c in hits.items():
                if c / len(eg) >= NGRAM_THRESHOLD:
                    flagged.append({"eval": eid, "train": [train_norm[i][0]],
                                    "reason": f"8gram_overlap={c / len(eg):.2f}"})
        else:
            for tid, t in train_norm:
                sm = difflib.SequenceMatcher(None, en, t)
                if sm.real_quick_ratio() >= CHAR_THRESHOLD and sm.ratio() >= CHAR_THRESHOLD:
                    flagged.append({"eval": eid, "train": [tid],
                                    "reason": f"char_similarity={sm.ratio():.2f}"})

    result = {"passed": not flagged, "n_train": len(train), "n_eval": len(evals),
              "flagged": flagged}
    out = ROOT / "results/contamination.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"train={len(train)} eval={len(evals)} flagged={len(flagged)} -> {out.name}")
    for f in flagged[:20]:
        print("  ", f)
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
