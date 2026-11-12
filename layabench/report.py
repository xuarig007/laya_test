"""Render a benchmark report as a Markdown summary, and diff two reports."""

from __future__ import annotations

from typing import Any

# Direction of "better" per metric; anything unlisted gets no verdict.
_LOWER_IS_BETTER = {
    "score_mae", "ece", "brier", "aurc",
    "latency_p50_ms", "latency_p95_ms", "cost_per_decision_p50_ms",
}
_HIGHER_IS_BETTER = {
    "choice_accuracy", "noul_accuracy",
    "selective_accuracy@50", "selective_accuracy@80",
}


def _direction(key: str, delta: float) -> str:
    if delta == 0:
        return ""
    if key in _LOWER_IS_BETTER:
        better = delta < 0
    elif key in _HIGHER_IS_BETTER or key.startswith("score_within_"):
        better = delta > 0
    else:
        return ""
    return " (better)" if better else " (worse)"

_ORDER = (
    "choice_accuracy",
    "noul_accuracy",
    "score_mae",
    "score_within_0.5",
    "mean_confidence",
    "ece",
    "brier",
    "aurc",
    "selective_accuracy@50",
    "selective_accuracy@80",
    "latency_p50_ms",
    "latency_p95_ms",
    "cost_per_decision_p50_ms",
    "n_answers",
    "n_scored",
)


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".") if value != int(value) else f"{int(value)}"
    return str(value)


def _metric_rows(block: dict[str, Any], keys: list[str]) -> list[str]:
    lines = []
    for key in keys:
        if key in block:
            label = "N/A" if block[key] is None else _fmt(block[key])
            lines.append(f"| `{key}` | {label} |")
    return lines


def _keys_of(block: dict[str, Any]) -> list[str]:
    present = [k for k in _ORDER if k in block]
    extra = [k for k in block if k not in _ORDER]
    return present + sorted(extra)


def render_markdown(report: dict[str, Any]) -> str:
    """Turn a report dict into a reviewable Markdown summary."""
    overall = report["overall"]
    lines: list[str] = []
    lines.append(f"# Laya triage benchmark - backend `{report['backend']}`")
    lines.append("")
    lines.append(f"- dataset: `{report['dataset']}`")
    lines.append(f"- rows: {report['n_rows']} | decisions: {overall.get('n_answers')} | scored: {overall.get('n_scored')}")
    lines.append(f"- noul asked as neutral-key choice: {report['noul_as_choice']}")
    lines.append("")

    lines.append("## Overall")
    lines.append("")
    lines.append("| metric | value |")
    lines.append("|---|---|")
    lines.extend(_metric_rows(overall, _keys_of(overall) or list(overall)))
    lines.append("")

    qi = report.get("slices", {}).get("qid")
    if qi:
        lines.append("## Per question")
        lines.append("")
        lines.append("| question | type | metric | value | n |")
        lines.append("|---|---|---|---|---|")
        for qid, block in qi.items():
            canon = "score" if "score_mae" in block else ("choice" if "choice_accuracy" in block else "noul")
            metric = {
                "choice": ("choice_accuracy", block.get("choice_accuracy")),
                "noul": ("noul_accuracy", block.get("noul_accuracy")),
                "score": ("score_mae", block.get("score_mae")),
            }[canon]
            lines.append(f"| {qid} | {canon} | `{metric[0]}` | {_fmt(metric[1])} | {block.get('n_answers')} |")
        lines.append("")

    lang = report.get("slices", {}).get("language")
    if lang:
        lines.append("## Per language")
        lines.append("")
        lines.append("| language | choice_acc | noul_acc | score_mae | ece | n |")
        lines.append("|---|---|---|---|---|---|")
        for name, block in lang.items():
            lines.append(
                f"| {name} | {_fmt(block.get('choice_accuracy'))} | {_fmt(block.get('noul_accuracy'))}"
                f" | {_fmt(block.get('score_mae'))} | {_fmt(block.get('ece'))} | {block.get('n_answers')} |"
            )
        lines.append("")

    lines.append("## Honest limits (from the Laya model card)")
    lines.append("")
    lines.append("- Base checkpoints are near chance zero-shot; this is a base to fine-tune.")
    lines.append("- Probabilities ship over-confident: refit a temperature per (type, option count) on your own data.")
    lines.append("- `noul` can follow its own true/false labels instead of the state; compare `--noul-as-choice`.")
    lines.append("- `action.act_probability` carries no usable signal yet; gate on confidence.")
    lines.append("")
    return "\n".join(lines)


def compare_reports(candidate: dict[str, Any], baseline: dict[str, Any], keys: list[str] | None = None) -> list[str]:
    """Return rows describing the delta of ``candidate`` against ``baseline``."""
    keys = keys or _keys_of(candidate["overall"])
    rows = []
    for key in keys:
        c = candidate["overall"].get(key)
        b = baseline["overall"].get(key)
        if c is None or b is None or isinstance(c, str) or isinstance(b, str):
            continue
        delta = c - b
        rows.append(f"| `{key}` | {_fmt(b)} | {_fmt(c)} | {delta:+.4f}{_direction(key, delta)} |")
    return rows
