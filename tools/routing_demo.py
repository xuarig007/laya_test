"""Show how the Laya router picks a checkpoint per ticket, without a forward pass.

    python tools/routing_demo.py

Uses ``Router.route()``, which decides on script/language alone and needs no
weights, so it runs fast after the checkpoints' metadata is available.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    from laya import Router

    states = [
        "I was charged twice for my March subscription, please refund me.",
        "J'ai été facturé deux fois pour mon abonnement de mars.",
        "Mir wurde der Betrag zweimal abgebucht.",
        "Me cobraron dos veces este mes, quiero que me devuelvan el dinero.",
        {"body": "मुझसे दो बार शुल्क लिया गया, कृपया पैसे वापस करें।", "channel": "email"},
        "Quero cancelar",  # very short Latin text: language undecided -> fallback
    ]

    router = Router()  # default="multilingual"
    print(f"{'state':<58} {'checkpoint':<13} reason")
    print("-" * 110)
    for state in states:
        decision = router.route(state)
        label = state if isinstance(state, str) else json.dumps(state, ensure_ascii=False)
        if len(label) > 55:
            label = label[:52] + "..."
        print(f"{label:<58} {decision.model:<13} {decision.reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
