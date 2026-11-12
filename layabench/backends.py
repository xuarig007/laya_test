"""Decision backends the benchmark compares.

Every backend exposes ``predict(state, questions) -> (answers, latency_ms)``
where ``answers[qid]`` is ``{"kind": <asked type>, "value": <label|prob|number>,
"confidence": float}``.

* :class:`LayaRouterBackend` - the real thing: ``laya.Router`` (needs the package
  and the checkpoints; routing picks the checkpoint per request).
* :class:`HeuristicBackend`   - a keyword/rule triage engine; the classic,
  weight-free baseline a team ships before reaching for a model.
* :class:`MajorityBackend`    - always the majority label; Laya's own
  ``majority-class`` reference line.
* :class:`RandomBackend`      - uniform random; Laya's own ``random`` line.
"""

from __future__ import annotations

import random
import time
from typing import Any

from . import schema

# --- Keyword tables for the rules baseline ----------------------------------
_DEPARTMENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "billing": (
        "bill", "factur", "charge", "refund", "rembours", "erstat", "cobr",
        "devolv", "reembols", "pago", "paiement", "zahlung", "precio", "price",
        "pay", "invoice", "subscription", "abonnement", "abo", "suscrip",
        "cancel", "kündig", "resili", "baja", "card", "carte", "kreditkarte",
        "tarjeta", "contrat", "vertrag",
    ),
    "technical": (
        "crash", "plant", "abstürz", "cierra", "error", "erreur", "fehler",
        "500", "403", "bug", "api", "integration", "intégration", "sync",
        "synchron", "upload", "export", "outage", "panne", "integr",
        "caída", "cai", "falla",
    ),
    "account": (
        "password", "mot de passe", "passwort", "contraseña", "login",
        "connexion", "anmelden", "2fa", "two-factor", "otp", "username",
        "profil", "profile", "compte", "konto", "cuenta", "access", "accès",
        "lock", "reset", "verrou",
    ),
}
_URGENT_KEYWORDS = (
    "immediately", "today", "now", "asap", "blocking", "outage", "crash",
    "aujourd", "immédiat", "résilie", "tout de suite", "sofort",
    "kündig", "sperre", "hoy", "inmediat", "cancelo", "urge", "crit",
    "can't", "cannot", "impossible", "gar nicht", "bloqu",
)
_PROBLEM_KEYWORDS = (
    "problem", "problème", "fehler", "error", "erreur", "issue", "fails",
    "fail", "ne fonctionne", "funktioniert nicht", "no puedo", "n'arrive",
)
_CHURN_KEYWORDS = (
    "cancel", "résilie", "resiliation", "résiliation", "kündig", "kündigung",
    "quitter", "leave", "churn", "competitor", "concurrent", "wettbewerb",
    "darme de baja", "cancelo", "baja", "wechseln", "stopping paying",
)
_REFUND_KEYWORDS = (
    "refund", "rembours", "erstat", "devolv", "reembols", "reembolso",
    "money back", "paiement", "zurück", "rembols", "charge twice", "twice",
    "double", "duplicate", "deux fois", "zweimal", "dos veces",
)


def _as_text(state: Any) -> str:
    if isinstance(state, str):
        return state
    if isinstance(state, dict):
        return " ".join(str(v) for v in state.values())
    return str(state)


def _match(text: str, keywords: tuple[str, ...]) -> bool:
    low = text.lower()
    return any(k in low for k in keywords)


def _parse_laya_answers(result: dict[str, Any], questions: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Normalise a Laya ``{"answers": ...}`` result into canonical records."""
    raw = result["answers"]
    answers: dict[str, dict[str, Any]] = {}
    for qid, question in questions.items():
        a = raw[qid]
        qtype = question["type"]
        if qtype == "choice":
            value = a["choice"]
            conf = a.get("answer_confidence", a.get("confidence", 1.0))
        elif qtype == "noul":
            value = float(a["noul"])
            conf = a.get("answer_confidence", max(value, 1.0 - value))
        else:  # score
            value = float(a["score"])
            conf = a.get("confidence", 1.0)
        answers[qid] = {"kind": qtype, "value": value, "confidence": float(conf)}
    return answers


class _BaseBackend:
    name = "base"

    def predict(self, state: Any, questions: dict[str, dict[str, Any]]):
        raise NotImplementedError


class LayaRouterBackend(_BaseBackend):
    """Real Laya: ``laya.Router`` routes each state to the right checkpoint."""

    name = "laya"

    def __init__(
        self,
        model: str | None = None,
        device: str | None = None,
        default: str | None = None,
        max_len: int | None = None,
        preload: bool = False,
    ) -> None:
        import laya  # imported lazily so the harness runs without the package

        kwargs: dict[str, Any] = {}
        if device:
            kwargs["device"] = device
        if default:
            kwargs["default"] = default
        if preload:
            kwargs["preload"] = True
        self.laya = laya
        self.router = laya.Router(**kwargs)
        self.model = model
        self.max_len = max_len

    def predict(self, state: Any, questions: dict[str, dict[str, Any]]):
        kwargs: dict[str, Any] = {}
        if self.model:
            kwargs["model"] = self.model
        if self.max_len:
            kwargs["max_len"] = self.max_len
        t0 = time.perf_counter()
        result = self.router.predict(state, questions, **kwargs)
        latency_ms = (time.perf_counter() - t0) * 1000.0
        return _parse_laya_answers(result, questions), latency_ms

    def warmup(self, state: Any, questions: dict[str, dict[str, Any]]) -> None:
        """One forward pass so the checkpoint load is not charged to the loop."""
        self.predict(state, questions)


class LayaAgentBackend(_BaseBackend):
    """A single checkpoint via ``laya.load`` + ``agent.predict`` (no routing).

    Use ``checkpoint`` for a fine-tuned directory or ``convaiinnovations/laya``
    with ``subfolder`` for one of the shipped checkpoints.
    """

    name = "agent"

    def __init__(
        self,
        checkpoint: str,
        subfolder: str | None = None,
        device: str | None = None,
    ) -> None:
        import laya

        kwargs: dict[str, Any] = {}
        if device:
            kwargs["device"] = device
        if subfolder:
            kwargs["subfolder"] = subfolder
        self.checkpoint = checkpoint
        self.agent = laya.load(checkpoint, **kwargs)

    def predict(self, state: Any, questions: dict[str, dict[str, Any]]):
        t0 = time.perf_counter()
        result = self.agent.predict(state, questions)
        latency_ms = (time.perf_counter() - t0) * 1000.0
        return _parse_laya_answers(result, questions), latency_ms

    def warmup(self, state: Any, questions: dict[str, dict[str, Any]]) -> None:
        self.predict(state, questions)


class HeuristicBackend(_BaseBackend):
    """A keyword/rule triage engine - deterministic and weight-free."""

    name = "heuristic"

    def predict(self, state: Any, questions: dict[str, dict[str, Any]]):
        t0 = time.perf_counter()
        text = _as_text(state)
        matched_dept = None
        best = 0
        for dept, kws in _DEPARTMENT_KEYWORDS.items():
            hits = sum(1 for k in kws if k in text.lower())
            if hits > best:
                best, matched_dept = hits, dept

        churn = _match(text, _CHURN_KEYWORDS)
        refund = _match(text, _REFUND_KEYWORDS)
        if _match(text, _URGENT_KEYWORDS):
            urgency = 2
        elif _match(text, _PROBLEM_KEYWORDS):
            urgency = 1
        else:
            urgency = 0

        answers: dict[str, dict[str, Any]] = {}
        for qid, question in questions.items():
            qtype = question["type"]  # the type as actually asked
            if qtype == "choice":
                if qid in schema.NOUL_AS_CHOICE:
                    flag = churn if qid == "churn_risk" else refund
                    kws = _CHURN_KEYWORDS if qid == "churn_risk" else _REFUND_KEYWORDS
                    value = "A" if flag else "B"
                    conf = 0.85 if _match(text, kws) else 0.6
                else:
                    value = matched_dept or "billing"
                    conf = 0.85 if matched_dept else 0.4
            elif qtype == "score":
                value = float(urgency)
                conf = 0.75
            else:  # noul
                flag = churn if qid == "churn_risk" else refund
                value = 0.85 if flag else 0.15
                conf = max(value, 1.0 - value)
            answers[qid] = {"kind": qtype, "value": value, "confidence": float(conf)}
        latency_ms = (time.perf_counter() - t0) * 1000.0
        return answers, latency_ms


class MajorityBackend(_BaseBackend):
    """Always answer the majority label seen in the dataset."""

    name = "majority"

    def __init__(self, expected_rows: list[dict[str, Any]]) -> None:
        from collections import Counter

        by_qid: dict[str, Counter] = {}
        for row in expected_rows:
            for qid, label in row["expected"].items():
                by_qid.setdefault(qid, Counter())[label] += 1
        self._majority: dict[str, Any] = {}
        self._rate: dict[str, float] = {}
        for qid, counter in by_qid.items():
            label, count = counter.most_common(1)[0]
            self._majority[qid] = label
            self._rate[qid] = count / sum(counter.values())

    def predict(self, state: Any, questions: dict[str, dict[str, Any]]):
        t0 = time.perf_counter()
        answers: dict[str, dict[str, Any]] = {}
        for qid, question in questions.items():
            canon = schema.CANONICAL_TYPE[qid]
            majority = self._majority[qid]
            conf = self._rate[qid]
            if canon == "score":
                value = float(majority)
            elif canon == "noul":
                bool_val = bool(majority)
                value = ("A" if bool_val else "B") if question["type"] == "choice" else (1.0 if bool_val else 0.0)
            else:  # choice
                value = majority
            answers[qid] = {"kind": question["type"], "value": value, "confidence": float(conf)}
        latency_ms = (time.perf_counter() - t0) * 1000.0
        return answers, latency_ms


class RandomBackend(_BaseBackend):
    """Uniform random over the labels, seeded for reproducibility."""

    name = "random"

    def __init__(self, seed: int = 13) -> None:
        self.rng = random.Random(seed)

    def predict(self, state: Any, questions: dict[str, dict[str, Any]]):
        t0 = time.perf_counter()
        answers: dict[str, dict[str, Any]] = {}
        for qid, question in questions.items():
            qtype = question["type"]  # the type as actually asked
            if qtype == "choice":
                if qid in schema.NOUL_AS_CHOICE:
                    value = self.rng.choice(["A", "B"])
                else:
                    value = self.rng.choice(list(schema.QUESTIONS[qid]["criteria"]))
            elif qtype == "score":
                value = float(self.rng.randint(0, len(schema.QUESTIONS[qid]["criteria"]) - 1))
            else:  # noul
                value = float(self.rng.choice([0.0, 1.0]))
            answers[qid] = {"kind": qtype, "value": value, "confidence": 0.5}
        latency_ms = (time.perf_counter() - t0) * 1000.0
        return answers, latency_ms


def build_backend(name: str, rows: list[dict[str, Any]], **kwargs: Any) -> _BaseBackend:
    """Construct a backend by name; ``rows`` seeds the majority baseline."""
    name = name.lower()
    if name in ("laya", "router"):
        return LayaRouterBackend(**kwargs)
    if name in ("agent", "single"):
        return LayaAgentBackend(**kwargs)
    if name == "heuristic":
        return HeuristicBackend()
    if name == "majority":
        return MajorityBackend(rows)
    if name == "random":
        return RandomBackend(seed=kwargs.get("seed", 13))
    raise ValueError(f"unknown backend {name!r}")
