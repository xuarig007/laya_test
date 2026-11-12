"""Metric implementations mirroring the ``laya.evals`` definitions.

Dependency-light on purpose (numpy only, never torch), exactly like the
reference harness, so the same numbers can be produced without a checkpoint.
Each function returns ``None`` on an empty input rather than publishing a
silent zero.

Conventions
-----------
* ``records`` is a list of ``(confidence, correct)`` pairs, where ``correct``
  is a bool.  ``confidence`` is the probability of the chosen answer
  (``answer_confidence`` where the checkpoint reports it, else ``confidence``).
* ``score`` answers have no ``correct`` value at any tolerance, so they never
  enter the confidence metrics (``ece``/``brier``/``aurc``/``selective_*``).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def _split(records: list[tuple[float, bool]]) -> tuple[NDArray, NDArray]:
    conf = np.array([c for c, _ in records], dtype=float)
    corr = np.array([1.0 if k else 0.0 for _, k in records], dtype=float)
    return conf, corr


def choice_accuracy(preds: list, expected: list) -> float | None:
    """Fraction of ``choice`` answers whose chosen label matches."""
    if not preds:
        return None
    return float(np.mean([p == e for p, e in zip(preds, expected)]))


def noul_accuracy(probs: list[float], expected: list) -> float | None:
    """Fraction of ``noul`` answers whose boolean (prob >= 0.5) matches."""
    if not probs:
        return None
    return float(np.mean([(float(p) >= 0.5) == bool(e) for p, e in zip(probs, expected)]))


def score_mae(preds: list[float], expected: list) -> float | None:
    """Mean absolute error over ``score`` answers."""
    if not preds:
        return None
    return float(np.mean([abs(float(p) - float(e)) for p, e in zip(preds, expected)]))


def score_within(preds: list[float], expected: list, tol: float) -> float | None:
    """Fraction of ``score`` answers within an absolute tolerance."""
    if not preds:
        return None
    return float(
        np.mean([abs(float(p) - float(e)) <= tol for p, e in zip(preds, expected)])
    )


def mean_confidence(records: list[tuple[float, bool]]) -> float | None:
    if not records:
        return None
    conf, _ = _split(records)
    return float(conf.mean())


def ece(records: list[tuple[float, bool]], n_bins: int = 15) -> float | None:
    """Expected calibration error, 15 bins by default."""
    if not records:
        return None
    conf, corr = _split(records)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(conf, edges[1:-1]), 0, n_bins - 1)
    n = len(conf)
    err = 0.0
    for b in range(n_bins):
        mask = idx == b
        if not mask.any():
            continue
        err += (mask.sum() / n) * abs(corr[mask].mean() - conf[mask].mean())
    return float(err)


def brier(records: list[tuple[float, bool]]) -> float | None:
    """Brier score of confidence as P(correct); lower is better."""
    if not records:
        return None
    conf, corr = _split(records)
    return float(np.mean((conf - corr) ** 2))


def aurc(records: list[tuple[float, bool]]) -> float | None:
    """Area under the risk-coverage curve; lower is better.

    One risk value per *distinct* confidence level, each weighted by the
    answers that level spans, so ties do not make the metric depend on row
    order (matching the ``laya.evals`` definition).
    """
    if not records:
        return None
    conf, corr = _split(records)
    order = np.argsort(-conf, kind="stable")
    conf, corr = conf[order], corr[order]
    n = len(conf)
    total = 0.0
    start = 0
    while start < n:
        end = start + 1
        while end < n and conf[end] == conf[start]:
            end += 1
        risk = (end - corr[:end].sum()) / end  # errors among the first `end`
        total += risk * ((end - start) / n)
        start = end
    return float(total)


def selective_accuracy(records: list[tuple[float, bool]], coverage: float = 0.5) -> float | None:
    """Accuracy over the answers a confidence threshold at ``coverage`` accepts.

    A threshold cannot split a group of equal confidences, so the accepted set
    can cover more than the named fraction.
    """
    if not records:
        return None
    conf, corr = _split(records)
    order = np.argsort(-conf, kind="stable")
    conf, corr = conf[order], corr[order]
    n = len(conf)
    k = max(1, min(int(np.ceil(coverage * n)), n))
    thr = conf[k - 1]
    accepted = conf >= thr
    return float(corr[accepted].mean())


def percentile(times_ms: list[float], q: float) -> float | None:
    """Percentile of per-request wall times, in milliseconds."""
    if not times_ms:
        return None
    return float(np.percentile(np.array(times_ms, dtype=float), q))
