"""Build a 100-ticket source file: the 33 hand-written tickets + 67 generated.

    python tools/gen_dataset.py

Writes ``data/tickets100.source.jsonl`` (compact source, same schema as
``data/tickets.source.jsonl``). The generated rows are assembled from curated
phrase banks per language, so each row's labels follow from the components used
to build it. They are *synthetic*: good enough to scale the fine-tuning
experiment, but the 33 hand-written tickets remain the higher-quality core.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

LANGS = ("en", "fr", "de", "es", "hi")
DEPTS = ("billing", "technical", "account")

# --- Phrase banks -----------------------------------------------------------
# The last billing entry per language is itself a refund request.
ISSUES: dict[str, dict[str, list[str]]] = {
    "billing": {
        "en": [
            "I was charged twice for my March subscription.",
            "The invoice for last month shows an amount I did not agree to.",
            "My card was billed after I downgraded my plan.",
            "I need to update the credit card on my account.",
            "I am requesting a full refund for last month's invoice.",
        ],
        "fr": [
            "J'ai été facturé deux fois pour mon abonnement de mars.",
            "La facture du mois dernier affiche un montant que je n'ai pas accepté.",
            "Ma carte a été débitée après mon passage à un forfait inférieur.",
            "Je souhaite mettre à jour la carte bancaire de mon compte.",
            "Je demande le remboursement intégral de la facture du mois dernier.",
        ],
        "de": [
            "Mir wurde der Märzbetrag zweimal abgebucht.",
            "Die Rechnung des letzten Monats zeigt einen Betrag, dem ich nicht zugestimmt habe.",
            "Meine Karte wurde nach dem Downgrade meines Tarifs belastet.",
            "Ich möchte die Kreditkarte in meinem Konto aktualisieren.",
            "Ich verlange eine vollständige Erstattung der letzten Rechnung.",
        ],
        "es": [
            "Me cobraron dos veces la suscripción de marzo.",
            "La factura del mes pasado muestra un importe que no acepté.",
            "Cobraron mi tarjeta después de bajar de plan.",
            "Necesito actualizar la tarjeta de mi cuenta.",
            "Solicito el reembolso completo de la factura del mes pasado.",
        ],
        "hi": [
            "मार्च की सदस्यता के लिए मुझसे दो बार शुल्क लिया गया।",
            "पिछले महीने के बिल में वह राशि है जिस पर मैं सहमत नहीं था।",
            "प्लान बदलने के बाद भी मेरे कार्ड से भुगतान हो गया।",
            "मुझे अपने खाते का क्रेडिट कार्ड बदलना है।",
            "मैं पिछले महीने के बिल का पूरा रिफंड मांगता हूँ।",
        ],
    },
}

ISSUES["technical"] = {
    "en": [
        "The app crashes every time I upload a photo.",
        "Our API returns a 500 error since this morning.",
        "The integration stopped syncing and records are missing.",
        "Exporting a report fails with an error.",
    ],
    "fr": [
        "L'application plante à chaque envoi de photo.",
        "Notre API renvoie une erreur 500 depuis ce matin.",
        "L'intégration ne se synchronise plus et des données manquent.",
        "L'export d'un rapport échoue avec une erreur.",
    ],
    "de": [
        "Die App stürzt bei jedem Foto-Upload ab.",
        "Unsere API liefert seit heute Morgen einen 500-Fehler.",
        "Die Integration synchronisiert nicht mehr und es fehlen Daten.",
        "Der Export eines Berichts schlägt mit einem Fehler fehl.",
    ],
    "es": [
        "La aplicación se cierra al subir una foto.",
        "Nuestra API devuelve un error 500 desde esta mañana.",
        "La integración dejó de sincronizar y faltan datos.",
        "Exportar un informe falla con un error.",
    ],
    "hi": [
        "फोटो अपलोड करते ही ऐप बंद हो जाता है।",
        "हमारी API आज सुबह से 500 त्रुटि दे रही है।",
        "इंटीग्रेशन सिंक करना बंद कर दिया और डेटा गायब है।",
        "रिपोर्ट निर्यात करने पर त्रुटि आती है।",
    ],
}

ISSUES["account"] = {
    "en": [
        "I forgot my password and the reset email never arrives.",
        "Two-factor login fails on my new phone.",
        "I need to update the email address on my profile.",
        "I cannot change my username.",
    ],
    "fr": [
        "J'ai oublié mon mot de passe et l'e-mail de réinitialisation n'arrive pas.",
        "La connexion à deux facteurs échoue sur mon nouveau téléphone.",
        "Je souhaite changer l'adresse e-mail de mon profil.",
        "Je n'arrive pas à modifier mon nom d'utilisateur.",
    ],
    "de": [
        "Ich habe mein Passwort vergessen und die Zurücksetzungs-E-Mail kommt nicht an.",
        "Die Zwei-Faktor-Anmeldung schlägt auf meinem neuen Telefon fehl.",
        "Ich möchte die E-Mail-Adresse in meinem Profil ändern.",
        "Ich kann meinen Benutzernamen nicht ändern.",
    ],
    "es": [
        "Olvidé mi contraseña y el correo de restablecimiento no llega.",
        "El acceso con dos factores falla en mi teléfono nuevo.",
        "Quiero cambiar el correo de mi perfil.",
        "No puedo cambiar mi nombre de usuario.",
    ],
    "hi": [
        "मैं अपना पासवर्ड भूल गया और रीसेट ईमेल नहीं आता।",
        "मेरे नए फ़ोन पर दो-चरणीय लॉगिन विफल हो जाता है।",
        "मुझे अपनी प्रोफ़ाइल का ईमेल बदलना है।",
        "मैं अपना उपयोगकर्ता नाम नहीं बदल सकता।",
    ],
}

URGENT = {
    "en": "This is blocking our whole team and needs a fix today.",
    "fr": "Tout notre service est bloqué, il faut corriger cela aujourd'hui.",
    "de": "Das blockiert unser ganzes Team und muss heute behoben werden.",
    "es": "Esto bloquea a todo nuestro equipo y hay que arreglarlo hoy.",
    "hi": "यह हमारी पूरी टीम को रोक रहा है और आज ठीक होना चाहिए।",
}
CALM = {
    "en": "No rush, whenever you get a chance.",
    "fr": "Pas d'urgence, quand vous pourrez.",
    "de": "Keine Eile, wenn Sie Zeit haben.",
    "es": "Sin prisa, cuando puedan.",
    "hi": "कोई जल्दी नहीं, जब समय मिले।",
}
REFUND = {
    "en": "Please refund the charge.",
    "fr": "Merci de me rembourser le montant.",
    "de": "Bitte erstatten Sie mir den Betrag.",
    "es": "Por favor, devuélvanme el importe.",
    "hi": "कृपया मुझे राशि वापस करें।",
}
CHURN = {
    "en": "Otherwise I will cancel my subscription.",
    "fr": "Sinon je résilie mon abonnement.",
    "de": "Andernfalls kündige ich mein Abonnement.",
    "es": "De lo contrario cancelaré mi suscripción.",
    "hi": "वरना मैं अपनी सदस्यता रद्द कर दूंगा।",
}

# The billing issue variant (by index) that is itself a refund request.
REFUND_ISSUE_INDEX = {"billing": 4}

TARGET = 100


def _generate(needed: int) -> list[dict]:
    """Deterministically build ``needed`` labelled tickets."""
    rows: list[dict] = []
    i = 0
    while len(rows) < needed:
        lang = LANGS[i % len(LANGS)]
        dept = DEPTS[(i // len(LANGS)) % len(DEPTS)]
        bank = ISSUES[dept][lang]
        variant = (i // (len(LANGS) * len(DEPTS))) % len(bank)
        parts = [bank[variant]]

        refund_ask = REFUND_ISSUE_INDEX.get(dept) == variant
        refund = refund_ask or (dept == "billing" and i % 2 == 0) or (i % 7 == 5)
        churn = i % 3 == 0
        urgency = 2 if i % 3 == 1 else (0 if i % 3 == 2 else 1)

        if refund and not refund_ask:
            parts.append(REFUND[lang])
        if churn:
            parts.append(CHURN[lang])
        if urgency == 2:
            parts.append(URGENT[lang])
        elif urgency == 0:
            parts.append(CALM[lang])

        rows.append(
            {
                "id": f"gen-{lang}-{i:03d}",
                "language": lang,
                "tags": [
                    t
                    for t, on in (
                        (dept, True),
                        ("refund", refund),
                        ("churn", churn),
                        ("urgent", urgency == 2),
                    )
                    if on
                ],
                "state": " ".join(parts),
                "expected": {
                    "department": dept,
                    "urgency": urgency,
                    "churn_risk": churn,
                    "refund_requested": refund,
                },
            }
        )
        i += 1
    return rows


def main() -> int:
    core = [
        json.loads(line)
        for line in (ROOT / "data" / "tickets.source.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip() and not line.startswith("#")
    ]
    rows = core + _generate(TARGET - len(core))
    out = ROOT / "data" / "tickets100.source.jsonl"
    out.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
    )

    print(f"wrote {out} ({len(rows)} rows: {len(core)} written + {len(rows) - len(core)} generated)")
    print("  language  ", dict(Counter(r["language"] for r in rows)))
    print("  department", dict(Counter(r["expected"]["department"] for r in rows)))
    print("  churn=true", sum(1 for r in rows if r["expected"]["churn_risk"]))
    print("  refund=true", sum(1 for r in rows if r["expected"]["refund_requested"]))
    print("  urgency   ", dict(Counter(r["expected"]["urgency"] for r in rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
