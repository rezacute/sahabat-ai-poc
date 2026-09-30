"""LoRA supervised fine-tuning of Sahabat-AI on the safety dataset.

Data format (data/train/safety_sft.jsonl), one JSON object per line:
  {"id": "...", "type": "refuse|helpful|general",
   "prompt":     [{"role": "user", "content": "..."}],
   "completion": [{"role": "assistant", "content": "..."}]}

The prompt/completion format makes TRL compute the loss on the assistant reply only.
Gemma 2's chat template has no system role, so do not add system messages.

    python scripts/train_sft.py --config config/train.yaml
"""
import argparse
import json
import pathlib

import torch
import yaml
from datasets import load_dataset
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from trl import SFTConfig, SFTTrainer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/train.yaml")
    args = ap.parse_args()
    cfg = yaml.safe_load(open(args.config))

    tok = AutoTokenizer.from_pretrained(cfg["base_model"])
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    quant = None
    if cfg.get("qlora"):
        quant = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
    # Gemma 2 uses logit soft-capping; eager attention is the safe choice for training.
    attn = "eager" if "gemma" in cfg["base_model"].lower() else "sdpa"
    model = AutoModelForCausalLM.from_pretrained(
        cfg["base_model"],
        torch_dtype=torch.bfloat16,
        quantization_config=quant,
        attn_implementation=attn,
        device_map={"": 0},
    )

    ds = load_dataset("json", data_files=cfg["train_file"], split="train")
    ds = ds.select_columns(["prompt", "completion"]).shuffle(seed=cfg["seed"])

    lora = cfg["lora"]
    peft_cfg = LoraConfig(
        r=lora["r"],
        lora_alpha=lora["alpha"],
        lora_dropout=lora["dropout"],
        target_modules=lora.get("target_modules", "all-linear"),
        task_type="CAUSAL_LM",
    )

    common = dict(
        output_dir=cfg["output_dir"],
        num_train_epochs=cfg["epochs"],
        per_device_train_batch_size=cfg["batch_size"],
        gradient_accumulation_steps=cfg["grad_accum"],
        learning_rate=cfg["lr"],
        lr_scheduler_type="cosine",
        warmup_ratio=cfg["warmup_ratio"],
        logging_steps=10,
        save_strategy="epoch",
        bf16=True,
        gradient_checkpointing=True,
        report_to="none",
        seed=cfg["seed"],
    )
    # TRL renamed max_seq_length -> max_length; support both.
    try:
        targs = SFTConfig(max_length=cfg["max_length"], **common)
    except TypeError:
        targs = SFTConfig(max_seq_length=cfg["max_length"], **common)

    trainer = SFTTrainer(
        model=model,
        args=targs,
        train_dataset=ds,
        processing_class=tok,
        peft_config=peft_cfg,
    )
    trainer.train()

    final = pathlib.Path(cfg["output_dir"]) / "final"
    trainer.save_model(str(final))
    tok.save_pretrained(str(final))
    (pathlib.Path(cfg["output_dir"]) / "loss_history.json").write_text(
        json.dumps(trainer.state.log_history, indent=2)
    )
    print(f"Adapter saved to {final}")


if __name__ == "__main__":
    main()
