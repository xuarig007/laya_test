"""The routing policy (typed question schema) and the eval-set loader.

One ticket -> four *typed* decisions, all answered in a single forward pass.
The three question types follow Laya's questions-and-answers contract:

* ``choice`` - pick one label out of ``criteria`` (a mapping label -> description);
* ``score``  - place the state on an ordered scale (``criteria`` is an ordered list);
* ``noul``   - the probability that the answer is yes (Laya's dedicated yes/no head).

The schema lives in one place so the dataset generator, the backends and the
harness all agree on it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# --- The routing policy: ticket -> {department, urgency, churn_risk, refund} --
# NOTE: this text is the *model contract* - it is exactly what the shipped
# checkpoints were trained on. Keep it stable; the human-readable explanation of
# every category lives in CATEGORY_GUIDE below and is shown by the tester page.
QUESTIONS: dict[str, dict[str, Any]] = {
    "department": {
        "type": "choice",
        "instructions": "Which team should handle this support ticket?",
        "criteria": {
            "billing": "double charges, invoices, payments, refunds, subscription price",
            "technical": "bugs, crashes, outages, errors, integration or API problems",
            "account": "login, password reset, two-factor auth, profile or access changes",
        },
    },
    "urgency": {
        "type": "score",
        "instructions": "How urgent is this ticket?",
        "criteria": ["low", "medium", "high"],
    },
    "churn_risk": {
        "type": "noul",
        "instructions": "Does the customer threaten to cancel, leave, or stop paying?",
    },
    "refund_requested": {
        "type": "noul",
        "instructions": "Is the customer explicitly asking to be refunded or paid back?",
    },
}

QUESTION_IDS: tuple[str, ...] = tuple(QUESTIONS)

# Canonical type of each question regardless of how it is *asked*.  The
# ``--noul-as-choice`` variant asks the two boolean questions as a two-option
# ``choice`` with neutral keys, but they stay boolean for scoring.
CANONICAL_TYPE: dict[str, str] = {
    "department": "choice",
    "urgency": "score",
    "churn_risk": "noul",
    "refund_requested": "noul",
}

# The documented workaround for noul following its own true/false labels
# (model card + questions-and-answers guide, issue #1244 / #156): ask the same
# thing as a two-option choice with neutral keys and the yes/no wording moved
# into the descriptions.
NOUL_AS_CHOICE: dict[str, dict[str, Any]] = {
    "churn_risk": {
        "type": "choice",
        "instructions": "Does the customer threaten to cancel, leave, or stop paying?",
        "criteria": {
            "A": "yes, the customer threatens to cancel or leave",
            "B": "no, the customer does not threaten to cancel or leave",
        },
    },
    "refund_requested": {
        "type": "choice",
        "instructions": "Is the customer explicitly asking to be refunded or paid back?",
        "criteria": {
            "A": "yes, a refund or payback is requested",
            "B": "no, no refund or payback is requested",
        },
    },
}


# --- Human-readable guide (display only; never sent to the model) ------------
# For each feature: the question in plain French and, for every category, its
# definition, the domain of application and the action it triggers downstream.
# The tester page renders this so a reader understands what each label means.
CATEGORY_GUIDE: dict[str, dict[str, Any]] = {
    "department": {
        "title": "Département",
        "type": "choice",
        "question": "Quelle équipe doit traiter ce ticket ?",
        "categories": [
            {
                "label": "billing",
                "definition": "Tout ce qui touche à l'argent : erreurs de facturation, doubles débits, "
                              "factures, moyens de paiement, changement de plan ou de prix, remboursements et avoirs.",
                "domain": "Finance / opérations de facturation",
                "action": "File « Facturation & encaissement »",
            },
            {
                "label": "technical",
                "definition": "Défauts produit et disponibilité : plantages, erreurs, pannes, échecs "
                              "d'intégration ou d'API, problèmes de synchronisation ou de données, performance.",
                "domain": "Ingénierie / support technique (SRE)",
                "action": "File « Ingénierie niveau 2 »",
            },
            {
                "label": "account",
                "definition": "Identité et accès : connexion, réinitialisation de mot de passe, "
                              "authentification à deux facteurs, changement d'e-mail, de pseudo ou de profil, "
                              "permissions et comptes bloqués.",
                "domain": "Gestion des identités et des accès (IAM)",
                "action": "File « Comptes & accès »",
            },
        ],
    },
    "urgency": {
        "title": "Urgence",
        "type": "score",
        "question": "Quel est le degré d'urgence du ticket ?",
        "categories": [
            {"label": "0", "definition": "Demande d'information ou sans échéance : une réponse standard suffit.",
             "domain": "Aucun impact opérationnel", "action": "Réponse sous 2 jours ouvrés (SLA standard)"},
            {"label": "1", "definition": "Le client est gêné ou bloqué sur une tâche, sans urgence critique.",
             "domain": "Impact utilisateur modéré", "action": "Réponse le jour même (SLA journée)"},
            {"label": "2", "definition": "Panne, perte de données ou de sécurité, ou blocage avec échéance le jour même.",
             "domain": "Impact fort / critique", "action": "Prise en charge immédiate (astreinte)"},
        ],
    },
    "churn_risk": {
        "title": "Risque de départ (churn)",
        "type": "noul",
        "question": "Le client menace-t-il de partir, de rétrograder ou d'arrêter de payer ?",
        "categories": [
            {"label": "oui", "definition": "Le texte exprime une intention de partir : « j'annule », "
             "« je résilie », « on passe à la concurrence », « réglez ça ou on part ».",
             "domain": "Rétention client", "action": "Alerte équipe rétention ; contact prioritaire."},
            {"label": "non", "definition": "Aucune intention de départ exprimée dans le texte.",
             "domain": "—", "action": "Aucune action de rétention."},
        ],
    },
    "refund_requested": {
        "title": "Demande de remboursement",
        "type": "noul",
        "question": "Le client demande-t-il explicitement à être remboursé ?",
        "categories": [
            {"label": "oui", "definition": "Le texte demande à récupérer de l'argent : remboursement, "
             "annulation de débit, avoir ou dédommagement.",
             "domain": "Politique de facturation", "action": "Déclencher la procédure de remboursement."},
            {"label": "non", "definition": "Simple réclamation sur un débit, sans demande de remboursement.",
             "domain": "—", "action": "Aucune action de remboursement."},
        ],
    },
}


def questions_for(noul_as_choice: bool = False) -> dict[str, dict[str, Any]]:
    """Return the policy, optionally asking the boolean questions as choice."""
    policy = {qid: dict(q) for qid, q in QUESTIONS.items()}
    if noul_as_choice:
        policy.update({qid: dict(q) for qid, q in NOUL_AS_CHOICE.items()})
    return policy


def build_questions(
    base: dict[str, dict[str, Any]], noul_as_choice: bool = False
) -> dict[str, dict[str, Any]]:
    """Swap every ``noul`` question in ``base`` for the neutral-key variant."""
    if not noul_as_choice:
        return base
    policy = {qid: dict(q) for qid, q in base.items()}
    for qid, q in base.items():
        if q.get("type") == "noul" and qid in NOUL_AS_CHOICE:
            policy[qid] = dict(NOUL_AS_CHOICE[qid])
    return policy


class DatasetError(ValueError):
    """Raised when an eval row is malformed, before any model call."""


def load_eval(path: str | Path) -> list[dict[str, Any]]:
    """Load a ``laya-evals`` style JSONL dataset, one JSON object per line.

    Blank lines and ``#`` comments are ignored.  Each row needs ``state``,
    ``questions`` and ``expected``; ``language`` and ``tags`` are optional and
    used for slicing.
    """
    rows: list[dict[str, Any]] = []
    for lineno, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise DatasetError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
        _validate_row(row, f"{path}:{lineno}")
        rows.append(row)
    if not rows:
        raise DatasetError(f"{path}: no eval rows found")
    return rows


def _validate_row(row: dict[str, Any], where: str) -> None:
    for key in ("state", "questions", "expected"):
        if key not in row:
            raise DatasetError(f"{where}: missing required field {key!r}")
    if not isinstance(row["questions"], dict) or not row["questions"]:
        raise DatasetError(f"{where}: 'questions' must be a non-empty object")
    if not isinstance(row["expected"], dict) or not row["expected"]:
        raise DatasetError(f"{where}: 'expected' must be a non-empty object")
    unknown = set(row["expected"]) - set(row["questions"])
    if unknown:
        raise DatasetError(
            f"{where}: 'expected' names questions not in 'questions': {sorted(unknown)}"
        )
