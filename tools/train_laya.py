"""Fine-tune Laya on the labelled tickets, on GPU or CPU (Python API).

    python tools/train_laya.py --data data/train100.jsonl --out checkpoints/tickets100-ft \
        --base multilingual --device cuda --epochs 15 --micro-batch 16 --grad-accum 1 \
        --calib-frac 0.25

Wraps ``laya.train.finetune``. Unlike the CLI it exposes ``calib_frac``, so the
calibration slice can be made large enough to actually fit temperatures on a
small dataset.
"""

from __future__ import annotations

import argparse
import dataclasses
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Fine-tune Laya on labelled decisions.")
    p.add_argument("--data", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--base", default="multilingual")
    p.add_argument("--eval", default=None, help="held-out dataset for before/after")
    p.add_argument("--device", default="cuda")
    p.add_argument("--epochs", type=int, default=15)
    p.add_argument("--micro-batch", type=int, default=16)
    p.add_argument("--grad-accum", type=int, default=1)
    p.add_argument("--encoder-lr", type=float, default=2.5e-5)
    p.add_argument("--head-lr", type=float, default=1e-4)
    p.add_argument("--loss", default="soft-ce", choices=["soft-ce", "rlcd"])
    p.add_argument("--label-smoothing", type=float, default=0.1)
    p.add_argument("--calib-frac", type=float, default=0.25)
    p.add_argument("--freeze-encoder", action="store_true")
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args(argv)

    from laya.train import TrainConfig, finetune

    wanted = {
        "epochs": args.epochs,
        "micro_batch": args.micro_batch,
        "grad_accum": args.grad_accum,
        "encoder_lr": args.encoder_lr,
        "head_lr": args.head_lr,
        "loss": args.loss,
        "label_smoothing": args.label_smoothing,
        "calib_frac": args.calib_frac,
        "freeze_encoder": args.freeze_encoder,
        "seed": args.seed,
    }
    if args.eval:
        wanted["eval_data"] = args.eval
    # Keep only the fields this Laya version actually defines.
    known = {f.name for f in dataclasses.fields(TrainConfig)}
    config = TrainConfig(**{k: v for k, v in wanted.items() if k in known})
    unknown = sorted(set(wanted) - known)
    if unknown:
        print(f"note: ignoring unsupported TrainConfig fields: {unknown}")

    print(f"fine-tuning {args.base} on {args.data} -> {args.out} (device={args.device})")
    report = finetune(
        args.data, args.base, args.out, config, device=args.device,
    )
    for key in ("train_items", "calibration_items", "optimizer_updates", "epoch_loss",
                "temperature", "calibration"):
        if key in report:
            print(f"{key}: {report[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
