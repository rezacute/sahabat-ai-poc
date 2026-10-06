#!/usr/bin/env bash
# Run SEA-HELM on one model. Use the SAME options for base and tuned.
#   scripts/run_seahelm.sh GoToCompany/gemma2-9b-cpt-sahabatai-v1-instruct results/seahelm_base
#   scripts/run_seahelm.sh "$PWD/merged/sft-v1"                     results/seahelm_tuned
#
# Notes
# - The tuned model must be the MERGED folder (scripts/merge_adapter.py), given as an absolute path.
# - MT-Bench needs OPENAI_API_KEY; translation needs Hugging Face access to MetricX-24.
#   If either is unavailable, exclude those tasks for BOTH runs and record the exact task list
#   in results/capability.json ("base_tasks" / "tuned_tasks").
# - Do NOT pass --base_model: these are instruction-tuned models.
set -euo pipefail
MODEL="$1"
OUT="$(realpath -m "$2")"
mkdir -p "$OUT"
cd "$(dirname "$0")/../third_party/SEA-HELM"
# The upstream `seahelm-evaluate` console script and `uv run seahelm_evaluation.py`
# both fail on this SEA-HELM snapshot: the entry point tries to import `main`
# from `src.seahelm_evaluation`, which does not exist. The `__main__` block in
# that file parses argv directly, so invoking the module with Python works.
# See logs/DEVIATIONS.md 2026-10-03 entry.
.venv/bin/python src/seahelm_evaluation.py \
  --tasks seahelm \
  --output_dir "$OUT" \
  --model_type vllm \
  --model_name "$MODEL" \
  --model_args "enable_prefix_caching=True,tensor_parallel_size=auto" \
  2>&1 | tee "$OUT/run.log"
