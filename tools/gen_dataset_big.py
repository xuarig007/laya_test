"""Build a larger dataset whose test set uses *unseen wording* (template holdout).

    python tools/gen_dataset_big.py --target 300

Every generated ticket carries a ``tpl`` id ``<language>-<department>-<realisation>``.
``tools/make_split.py --strategy template`` then holds out one whole realisation per
(language, department), so the held-out tickets are phrased with templates that never
appear in training. That turns the fine-tuning result into a **generalisation** result
rather than a memorisation one. Phrase banks are reused from ``tools/gen_dataset.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from gen_dataset import CALM, CHURN, DEPTS, ISSUES, LANGS, REFUND, URGENT  # noqa: E402

# (refund, churn, urgency) combinations cycled inside every (language, department) cell.
PATTERNS = [
    (False, False, 1),
    (True, False, 1),
    (False, True, 2),
    (False, False, 0),
    (True, True, 2),
]
N_VARIANTS = 4  # realisations per (language, department); the last is held out


def _ticket(lang: str, dept: str, variant: int, pattern: tuple, idx: int) -> dict:
    refund, churn, urgency = pattern
    parts = [ISSUES[dept][lang][variant]]
    if refund:
        parts.append(REFUND[lang])
    if churn:
        parts.append(CHURN[lang])
    if urgency == 2:
        parts.append(URGENT[lang])
    elif urgency == 0:
        parts.append(CALM[lang])
    return {
        "id": f"big-{lang}-{idx:04d}",
        "language": lang,
        "tpl": f"{lang}-{dept}-{variant}",
        "tags": [
            t for t, on in ((dept, True), ("refund", refund), ("churn", churn),
                            ("urgent", urgency == 2)) if on
        ],
        "state": " ".join(parts),
        "expected": {
            "department": dept,
            "urgency": urgency,
            "churn_risk": churn,
            "refund_requested": refund,
        },
    }


def _generate(target: int) -> list[dict]:
    rows: list[dict] = []
    idx = 0
    for variant in range(N_VARIANTS):
        for lang in LANGS:
            for dept in DEPTS:
                for pattern in PATTERNS:
                    if len(rows) >= target:
                        return rows
                    rows.append(_ticket(lang, dept, variant, pattern, idx))
                    idx += 1
    return rows


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build a template-held-out dataset.")
    p.add_argument("--target", type=int, default=300)
    p.add_argument("--out", default="data/tickets300.source.jsonl")
    args = p.parse_args(argv)

    core = [
        json.loads(line)
        for line in (ROOT / "data" / "tickets.source.jsonl")
        .read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    rows = core + _generate(args.target)
    out = ROOT / args.out
    out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                   encoding="utf-8")

    print(f"wrote {out} ({len(rows)} rows: {len(core)} written + {len(rows) - len(core)} generated)")
    print("  language  ", dict(Counter(r["language"] for r in rows)))
    print("  department", dict(Counter(r["expected"]["department"] for r in rows)))
    print("  churn=true", sum(1 for r in rows if r["expected"]["churn_risk"]))
    print("  refund=true", sum(1 for r in rows if r["expected"]["refund_requested"]))
    print("  urgency   ", dict(Counter(r["expected"]["urgency"] for r in rows)))
    print("  templates ", len({r["tpl"] for r in rows if r.get("tpl")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
