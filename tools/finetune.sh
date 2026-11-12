#!/usr/bin/env bash
# Fine-tune Laya on our labelled tickets, then evaluate the result.
#
#   bash tools/finetune.sh            # frozen encoder (fast on CPU)
#   FREEZE="" bash tools/finetune.sh  # full fine-tune (slower on CPU)
#
# Produces checkpoints/tickets-ft and prints Laya's own before/after table.
# Evaluate the checkpoint with our harness afterwards:
#   .venv/bin/python -m layabench run --data data/test.jsonl --backend agent \
#       --checkpoint checkpoints/tickets-ft --device cpu --warmup \
#       --json results/after_ft_test.json --markdown results/after_ft_test.md
set -euo pipefail
cd "$(dirname "$0")/.."

FREEZE="${FREEZE:---freeze-encoder}"
OUT="${OUT:-checkpoints/tickets-ft}"

.venv/bin/python tools/make_split.py

# shellcheck disable=SC2086
.venv/bin/laya-train \
    --data data/train.jsonl \
    --eval data/test.jsonl \
    --base multilingual \
    --out "$OUT" \
    --loss soft-ce \
    --label-smoothing 0.1 \
    $FREEZE \
    --epochs 30 \
    --micro-batch 8 \
    --grad-accum 4 \
    --device cpu \
    --seed 0
