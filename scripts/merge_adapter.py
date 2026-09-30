"""Merge the LoRA adapter into full bf16 weights so SEA-HELM can load it as a normal model.

    python scripts/merge_adapter.py --base GoToCompany/gemma2-9b-cpt-sahabatai-v1-instruct \
        --adapter runs/sft-v1/final --out merged/sft-v1
"""
import argparse

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

ap = argparse.ArgumentParser()
ap.add_argument("--base", required=True)
ap.add_argument("--adapter", required=True)
ap.add_argument("--out", required=True)
args = ap.parse_args()

model = AutoModelForCausalLM.from_pretrained(args.base, torch_dtype=torch.bfloat16, device_map={"": 0})
model = PeftModel.from_pretrained(model, args.adapter).merge_and_unload()
model.save_pretrained(args.out, safe_serialization=True)
AutoTokenizer.from_pretrained(args.base).save_pretrained(args.out)
print(f"Merged model written to {args.out}")
