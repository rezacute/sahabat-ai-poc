#!/usr/bin/env bash
# Environment setup for an NVIDIA RTX PRO 6000 (Blackwell, 96 GB, compute capability 12.0).
# Blackwell needs CUDA 12.8+ builds of PyTorch, vLLM and bitsandbytes. If any step fails with
# "no kernel image is available" or "sm_120", upgrade that package to its newest release.
#
# Three separate environments avoid version clashes (vLLM pins its own torch):
#   .venv-train   training + merging (torch, transformers, peft, trl)
#   .venv-infer   generation, judging, gate check (vllm, openai, numpy)
#   SEA-HELM      its own uv environment inside third_party/SEA-HELM
set -euo pipefail

nvidia-smi
python3 --version

echo "== training env =="
python3 -m venv .venv-train
.venv-train/bin/pip install -U pip
.venv-train/bin/pip install torch --index-url https://download.pytorch.org/whl/cu128
.venv-train/bin/pip install -r requirements-train.txt
.venv-train/bin/python -c "import torch; print('torch', torch.__version__, 'cuda', torch.version.cuda, 'cap', torch.cuda.get_device_capability())"

echo "== inference env =="
python3 -m venv .venv-infer
.venv-infer/bin/pip install -U pip
.venv-infer/bin/pip install -r requirements-infer.txt
.venv-infer/bin/python -c "import vllm, torch; print('vllm', vllm.__version__, 'torch', torch.__version__, 'cap', torch.cuda.get_device_capability())"

echo "== SEA-HELM =="
mkdir -p third_party
if [ ! -d third_party/SEA-HELM ]; then
  git clone https://github.com/aisingapore/SEA-HELM third_party/SEA-HELM
fi
command -v uv >/dev/null || pip install uv
(cd third_party/SEA-HELM && uv sync)

echo "Setup complete. Remember: export HF_TOKEN=... (gated models) before running."
