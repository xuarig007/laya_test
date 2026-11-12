"""Deterministic, documented train/test split for the fine-tuning experiment.

    python tools/make_split.py

Writes ``data/train.jsonl`` and ``data/test.jsonl`` in the canonical
``laya-evals`` format. The held-out ids are fixed below so the "before" and
"after" numbers are measured on the *same* cases and the split is reproducible.

The test set is chosen on purpose, not at random:
* it covers all five languages and all three departments;
* it keeps 4 of the 7 ``churn_risk=true`` cases and 3 of the 8
  ``refund_requested=true`` cases, so the weak spots we found in the zero-shot
  run are actually measurable after fine-tuning;
* the training set still carries examples of every label (including churn and
  refund true), so nothing is unlearnable.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from layabench.schema import load_eval  # noqa: E402

# Held-out cases for the 33-ticket set (10 of 33): chosen, not random, to keep
# all languages, all departments and 4 of the 7 churn threats in the test set.
TEST_IDS = frozenset(
    {
        "en-02", "en-06", "en-09",
        "fr-02", "fr-04",
        "de-04", "de-06",
        "es-02", "es-07",
        "hi-01",
    }
)


def _stratified_split(rows: list[dict], holdout_frac: float) -> set[str]:
    """Deterministic per-language strided holdout; scales to any dataset size."""
    test_ids: set[str] = set()
    for lang in sorted({r["language"] for r in rows}):
        ids = sorted(r["id"] for r in rows if r["language"] == lang)
        step = max(2, round(1 / holdout_frac))
        for idx, rid in enumerate(ids):
            if idx % step == 0:
                test_ids.add(rid)
    return test_ids


def _template_split(rows: list[dict]) -> set[str]:
    """Hold out one whole realisation per (language, department): unseen wording.

    Requires rows carrying a ``tpl`` field (see ``tools/gen_dataset_big.py``).
    Rows without a ``tpl`` (hand-written) always stay in train.
    """
    by_cell: dict[tuple[str, str], set[int]] = {}
    for r in rows:
        tpl = r.get("tpl")
        if not tpl:
            continue
        lang, dept, var = tpl.rsplit("-", 2)
        by_cell.setdefault((lang, dept), set()).add(int(var))
    holdout = {f"{lang}-{dept}-{max(v)}" for (lang, dept), v in by_cell.items() if v}
    return {r["id"] for r in rows if r.get("tpl") in holdout}


def _counts(rows: list[dict]) -> dict[str, Counter]:
    by_lang: Counter = Counter(r["language"] for r in rows)
    by_dept: Counter = Counter(r["expected"]["department"] for r in rows)
    churn = sum(1 for r in rows if r["expected"]["churn_risk"])
    refund = sum(1 for r in rows if r["expected"]["refund_requested"])
    return {"language": by_lang, "department": by_dept,
            "churn_true": Counter({"true": churn, "false": len(rows) - churn}),
            "refund_true": Counter({"true": refund, "false": len(rows) - refund})}


def _write(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic train/test split.")
    parser.add_argument("--data", default="data/tickets.eval.jsonl")
    parser.add_argument("--train-out", default="data/train.jsonl")
    parser.add_argument("--test-out", default="data/test.jsonl")
    parser.add_argument("--strategy", choices=["explicit", "stratified", "template"],
                        default="explicit")
    parser.add_argument("--holdout-frac", type=float, default=0.2,
                        help="held-out fraction per language (stratified strategy)")
    args = parser.parse_args(argv)

    rows = load_eval(ROOT / args.data)
    known = {r["id"] for r in rows}
    if args.strategy == "explicit":
        unknown = TEST_IDS - known
        if unknown:
            raise SystemExit(f"test ids not in the dataset: {sorted(unknown)}")
        test_ids = set(TEST_IDS)
    elif args.strategy == "stratified":
        test_ids = _stratified_split(rows, args.holdout_frac)
    else:  # template
        test_ids = _template_split(rows)

    train = [r for r in rows if r["id"] not in test_ids]
    test = [r for r in rows if r["id"] in test_ids]
    _write(ROOT / args.train_out, train)
    _write(ROOT / args.test_out, test)

    print(f"data  : {args.data} ({len(rows)} rows, strategy={args.strategy})")
    print(f"train : {len(train)} rows  ->  {args.train_out}")
    print(f"test  : {len(test)} rows  ->  {args.test_out}")
    for name, part in (("train", train), ("test", test)):
        c = _counts(part)
        print(f"\n[{name}]")
        print("  language   ", dict(c["language"]))
        print("  department ", dict(c["department"]))
        print("  churn=true ", dict(c["churn_true"]))
        print("  refund=true", dict(c["refund_true"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
