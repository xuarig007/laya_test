"""Build the canonical ``laya-evals`` JSONL from the compact source file.

    python tools/build_dataset.py

Reads  ``data/tickets.source.jsonl``  (id, state, language, tags, expected)
Writes ``data/tickets.eval.jsonl``    (state, questions, expected, language, tags)

The question schema is injected from :mod:`layabench.schema`, so the dataset and
the harness can never disagree about the policy being evaluated.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from layabench import schema  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a canonical laya-evals JSONL from a compact source.")
    parser.add_argument("--source", default="data/tickets.source.jsonl")
    parser.add_argument("--out", default="data/tickets.eval.jsonl")
    args = parser.parse_args(argv)

    src = ROOT / args.source
    dst = ROOT / args.out
    questions = schema.questions_for(noul_as_choice=False)

    rows = []
    for line in src.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        row = json.loads(line)
        record = {
            "id": row["id"],
            "state": row["state"],
            "questions": questions,
            "expected": row["expected"],
            "language": row.get("language"),
            "tags": row.get("tags", []),
        }
        if "tpl" in row:
            record["tpl"] = row["tpl"]
        rows.append(record)

    dst.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {dst} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
