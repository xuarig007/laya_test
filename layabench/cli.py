"""Command line: ``python -m layabench [run|validate|compare] ...``.

Examples
--------
    # score the labelled set with the rules baseline (no weights needed)
    python -m layabench run --data data/tickets.eval.jsonl --backend heuristic

    # score it with the real engine, auto-routing per language
    python -m layabench run --data data/tickets.eval.jsonl --backend laya \\
        --device cpu --json results/laya.json --markdown results/laya.md

    # measure the documented noul workaround
    python -m layabench run --data data/tickets.eval.jsonl --backend laya --noul-as-choice

    # gate a change against a saved baseline
    python -m layabench compare results/laya.json --baseline results/baseline.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, backends, harness, report, schema


def _cmd_validate(args: argparse.Namespace) -> int:
    try:
        rows = schema.load_eval(args.data)
    except schema.DatasetError as exc:
        print(f"INVALID: {exc}")
        return 2
    print(f"OK: {len(rows)} rows; questions={sorted(rows[0]['questions'])}")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    rows = schema.load_eval(args.data)
    kwargs: dict = {}
    if args.backend in ("laya", "router"):
        kwargs = {
            "model": args.model,
            "device": args.device,
            "default": args.default_model,
            "max_len": args.max_len,
        }
    elif args.backend in ("agent", "single"):
        if not args.checkpoint:
            print("error: --backend agent requires --checkpoint", file=sys.stderr)
            return 2
        kwargs = {
            "checkpoint": args.checkpoint,
            "subfolder": args.subfolder,
            "device": args.device,
        }
    within = tuple(args.within) if args.within else (0.5,)
    backend = backends.build_backend(args.backend, rows, **kwargs)
    if args.warmup and hasattr(backend, "warmup"):
        backend.warmup(rows[0]["state"], schema.build_questions(rows[0]["questions"], args.noul_as_choice))
    rep = harness.run(
        args.data, backend, within=within, noul_as_choice=args.noul_as_choice
    )
    text = report.render_markdown(rep)
    print(text)
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nwrote {args.json}")
    if args.markdown:
        Path(args.markdown).parent.mkdir(parents=True, exist_ok=True)
        Path(args.markdown).write_text(text, encoding="utf-8")
        print(f"wrote {args.markdown}")
    return 0


def _cmd_compare(args: argparse.Namespace) -> int:
    candidate = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    rows = report.compare_reports(candidate, baseline)
    print(f"# compare `{candidate['backend']}` (candidate) vs `{baseline['backend']}` (baseline)")
    print()
    print("| metric | baseline | candidate | delta |")
    print("|---|---|---|---|")
    print("\n".join(rows))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="layabench",
        description="Multilingual support-ticket triage benchmark for Laya",
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="check a JSONL eval set without a model")
    v.add_argument("data")
    v.set_defaults(func=_cmd_validate)

    r = sub.add_parser("run", help="score a dataset with a decision backend")
    r.add_argument("--data", required=True)
    r.add_argument(
        "--backend",
        default="heuristic",
        choices=["laya", "router", "agent", "single", "heuristic", "majority", "random"],
    )
    r.add_argument("--checkpoint", help="checkpoint dir or hub id (for --backend agent)")
    r.add_argument("--subfolder", help="subfolder of the hub repo (e.g. multilingual)")
    r.add_argument("--model", help="force a Laya checkpoint (english|multilingual|typed-decisions)")
    r.add_argument("--device", help="e.g. cpu, cuda")
    r.add_argument("--default-model", dest="default_model", help="routing fallback checkpoint")
    r.add_argument("--max-len", dest="max_len", type=int, help="token budget for long states")
    r.add_argument("--within", type=float, action="append", help="score tolerance (repeatable)")
    r.add_argument("--noul-as-choice", dest="noul_as_choice", action="store_true",
                   help="ask the boolean questions as neutral-key choice questions")
    r.add_argument("--warmup", action="store_true",
                   help="run one forward pass first so model load is not timed")
    r.add_argument("--json", help="write the full report as JSON")
    r.add_argument("--markdown", help="write the Markdown summary")
    r.set_defaults(func=_cmd_run)

    c = sub.add_parser("compare", help="diff a report against a baseline")
    c.add_argument("candidate")
    c.add_argument("--baseline", required=True)
    c.set_defaults(func=_cmd_compare)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
