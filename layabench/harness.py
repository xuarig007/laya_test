"""Run a labelled dataset against a backend and produce a metrics report.

The harness is backend-agnostic: it asks each backend for canonical answers,
scores them exactly as ``laya.evals`` would (see :mod:`layabench.metrics`) and
aggregates overall, per question and per slice (language, tag).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from . import metrics, schema
from .schema import CANONICAL_TYPE, build_questions, load_eval


def _record(qid: str, expected: Any, answer: dict[str, Any]) -> dict[str, Any]:
    """Turn one backend answer into a canonical, scoreable record."""
    canon = CANONICAL_TYPE[qid]
    rec: dict[str, Any] = {
        "qid": qid,
        "canon": canon,
        "kind": answer["kind"],
        "confidence": float(answer["confidence"]),
        "correct": None,
    }
    if canon == "choice":
        rec["pred"] = answer["value"]
        rec["expected"] = expected
        rec["correct"] = answer["value"] == expected
    elif canon == "score":
        rec["pred"] = float(answer["value"])
        rec["expected"] = float(expected)
    else:  # noul, possibly asked as a neutral-key choice
        if answer["kind"] == "choice":
            prob = 1.0 if str(answer["value"]).strip().upper().startswith("A") else 0.0
        else:
            prob = float(answer["value"])
        rec["prob"] = prob
        rec["expected"] = bool(expected)
        rec["correct"] = (prob >= 0.5) == bool(expected)
    return rec


def summarize(records: list[dict[str, Any]], within: tuple[float, ...]) -> dict[str, Any]:
    """Compute the metric block for a list of scoreable records."""
    out: dict[str, Any] = {}
    choice = [r for r in records if r["canon"] == "choice"]
    noul = [r for r in records if r["canon"] == "noul"]
    score = [r for r in records if r["canon"] == "score"]

    if choice:
        out["choice_accuracy"] = metrics.choice_accuracy(
            [r["pred"] for r in choice], [r["expected"] for r in choice]
        )
    if noul:
        out["noul_accuracy"] = metrics.noul_accuracy(
            [r["prob"] for r in noul], [r["expected"] for r in noul]
        )
    if score:
        preds = [r["pred"] for r in score]
        exps = [r["expected"] for r in score]
        out["score_mae"] = metrics.score_mae(preds, exps)
        for tol in within:
            out[f"score_within_{tol}"] = metrics.score_within(preds, exps, tol)

    conf = [(r["confidence"], r["correct"]) for r in records if r["correct"] is not None]
    if conf:
        out["mean_confidence"] = metrics.mean_confidence(conf)
        out["ece"] = metrics.ece(conf)
        out["brier"] = metrics.brier(conf)
        out["aurc"] = metrics.aurc(conf)
        out["selective_accuracy@50"] = metrics.selective_accuracy(conf, 0.5)
        out["selective_accuracy@80"] = metrics.selective_accuracy(conf, 0.8)

    out["n_answers"] = len(records)
    out["n_scored"] = len(conf)
    return out


def run(
    dataset_path: str,
    backend: Any,
    within: tuple[float, ...] = (0.5,),
    noul_as_choice: bool = False,
    slice_keys: tuple[str, ...] = ("language", "qid", "tag"),
) -> dict[str, Any]:
    """Score ``dataset_path`` with ``backend`` and return a report dictionary."""
    rows = load_eval(dataset_path)
    records: list[dict[str, Any]] = []
    latencies: list[float] = []
    rows_detail: list[dict[str, Any]] = []

    for row in rows:
        questions = build_questions(row["questions"], noul_as_choice)
        answers, latency_ms = backend.predict(row["state"], questions)
        latencies.append(latency_ms)

        row_records: list[dict[str, Any]] = []
        for qid, expected in row["expected"].items():
            rec = _record(qid, expected, answers[qid])
            rec["language"] = row.get("language")
            rec["tags"] = list(row.get("tags", []))
            records.append(rec)
            row_records.append(rec)
        rows_detail.append(
            {
                "id": row.get("id"),
                "language": row.get("language"),
                "state": row["state"],
                "records": row_records,
            }
        )

    decisions_per_row = [len(r["expected"]) for r in rows]
    overall = summarize(records, within)
    overall["latency_p50_ms"] = metrics.percentile(latencies, 50)
    overall["latency_p95_ms"] = metrics.percentile(latencies, 95)
    overall["cost_per_decision_p50_ms"] = metrics.percentile(
        [lat / n for lat, n in zip(latencies, decisions_per_row)], 50
    )

    slices: dict[str, dict[str, Any]] = {}
    for key in slice_keys:
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for rec in records:
            if key == "language":
                groups[rec["language"] or "unknown"].append(rec)
            elif key == "qid":
                groups[rec["qid"]].append(rec)
            elif key == "tag":
                for tag in rec["tags"]:
                    groups[tag].append(rec)
        if groups:
            slices[key] = {name: summarize(g, within) for name, g in sorted(groups.items())}

    return {
        "schema": "layabench-report/1",
        "backend": getattr(backend, "name", "unknown"),
        "dataset": str(dataset_path),
        "n_rows": len(rows),
        "noul_as_choice": noul_as_choice,
        "within": list(within),
        "questions": schema.questions_for(noul_as_choice),
        "overall": overall,
        "slices": slices,
        "rows": rows_detail,
    }
