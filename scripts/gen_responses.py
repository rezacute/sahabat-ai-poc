"""Generate model answers for the eval sets with vLLM (greedy decoding, reproducible).

Base model:
    python scripts/gen_responses.py --tag base \
        --inputs harmful=data/eval/safety_harmful.jsonl benign=data/eval/overrefusal_benign.jsonl \
        --out results/responses_base.jsonl
Tuned model (base + LoRA adapter, no merge needed):
    python scripts/gen_responses.py --tag tuned --adapter runs/sft-v1/final \
        --inputs harmful=data/eval/safety_harmful.jsonl benign=data/eval/overrefusal_benign.jsonl \
        --out results/responses_tuned.jsonl
"""
import argparse
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import read_jsonl, verify_lock, write_jsonl  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="GoToCompany/gemma2-9b-cpt-sahabatai-v1-instruct")
    ap.add_argument("--adapter", default=None)
    ap.add_argument("--tag", required=True, choices=["base", "tuned"])
    ap.add_argument("--inputs", nargs="+", required=True, help="name=path pairs")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max_tokens", type=int, default=768)
    args = ap.parse_args()

    ok, problems = verify_lock()
    if not ok:
        sys.exit("Refusing to generate: " + "; ".join(problems))

    from vllm import LLM, SamplingParams
    from vllm.lora.request import LoRARequest

    llm = LLM(
        model=args.base,
        dtype="bfloat16",
        max_model_len=4096,
        enable_lora=bool(args.adapter),
        max_lora_rank=64,
        seed=0,
    )
    sp = SamplingParams(temperature=0.0, max_tokens=args.max_tokens)
    lora = LoRARequest("tuned", 1, args.adapter) if args.adapter else None

    out_rows = []
    for pair in args.inputs:
        name, path = pair.split("=", 1)
        rows = read_jsonl(path)
        convs = [[{"role": "user", "content": r["prompt"]}] for r in rows]  # no system role for Gemma 2
        outs = llm.chat(convs, sp, lora_request=lora, use_tqdm=True)
        for r, o in zip(rows, outs):
            out_rows.append({
                "id": r["id"], "set": name, "category": r.get("category"),
                "lang": r.get("lang"), "prompt": r["prompt"],
                "response": o.outputs[0].text, "model_tag": args.tag,
            })
    write_jsonl(args.out, out_rows)
    print(f"{len(out_rows)} responses -> {args.out}")


if __name__ == "__main__":
    main()
