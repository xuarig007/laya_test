"""Translations for the web tester: UI strings and the category guide, in the
five languages of the demo dataset (EN / FR / DE / ES / HI).

    from layabench.i18n import LANGUAGES, UI, GUIDE

The page sends the language it wants (``GET /i18n?lang=de``) and re-renders: the
question titles, the column headers, the badges and the whole category guide
follow the chosen language.

This is display-only data; it is never sent to the model (the model contract
lives in :mod:`layabench.schema`).
"""

from __future__ import annotations

LANGUAGES = ("en", "fr", "de", "es", "hi")
DEFAULT_LANGUAGE = "en"

UI: dict[str, dict[str, str]] = {
    "en": {
        "header": "Support-ticket triage — fine-tuned Laya model",
        "ticket_label": "Ticket (text or JSON document)",
        "analyze": "Analyze",
        "guide_closed": "Category guide ▾",
        "guide_open": "Category guide ▴",
        "placeholder": "The result will appear here.",
        "base_col": "Without fine-tuning (base)",
        "ft_col": "With fine-tuning",
        "confidence": "confidence",
        "differs": "differs",
        "same": "same",
        "yes": "Yes",
        "no": "No",
        "of_yes": 'of "yes"',
        "error": "Error",
        "models_unavailable": "models unavailable",
        "ready": "ready",
        "guide_col_category": "Category",
        "guide_col_definition": "Definition",
        "guide_col_domain": "Domain of application",
        "guide_col_action": "Downstream action",
    },
    "fr": {
        "header": "Triage de tickets — modèle Laya fine-tuné",
        "ticket_label": "Ticket (texte ou document JSON)",
        "analyze": "Analyser",
        "guide_closed": "Guide des catégories ▾",
        "guide_open": "Guide des catégories ▴",
        "placeholder": "Le résultat s'affichera ici.",
        "base_col": "Sans fine-tuning (base)",
        "ft_col": "Avec fine-tuning",
        "confidence": "confiance",
        "differs": "écart",
        "same": "idem",
        "yes": "Oui",
        "no": "Non",
        "of_yes": "de « oui »",
        "error": "Erreur",
        "models_unavailable": "modèles indisponibles",
        "ready": "prêt",
        "guide_col_category": "Catégorie",
        "guide_col_definition": "Définition",
        "guide_col_domain": "Domaine d'application",
        "guide_col_action": "Action en aval",
    },
    "de": {
        "header": "Support-Ticket-Triage — feinabgestimmtes Laya-Modell",
        "ticket_label": "Ticket (Text oder JSON-Dokument)",
        "analyze": "Analysieren",
        "guide_closed": "Kategorie-Leitfaden ▾",
        "guide_open": "Kategorie-Leitfaden ▴",
        "placeholder": "Das Ergebnis erscheint hier.",
        "base_col": "Ohne Feintuning (Basis)",
        "ft_col": "Mit Feintuning",
        "confidence": "Konfidenz",
        "differs": "Abweichung",
        "same": "gleich",
        "yes": "Ja",
        "no": "Nein",
        "of_yes": "für „Ja“",
        "error": "Fehler",
        "models_unavailable": "Modelle nicht verfügbar",
        "ready": "bereit",
        "guide_col_category": "Kategorie",
        "guide_col_definition": "Definition",
        "guide_col_domain": "Anwendungsbereich",
        "guide_col_action": "Folgeaktion",
    },
    "es": {
        "header": "Triaje de tickets — modelo Laya ajustado",
        "ticket_label": "Ticket (texto o documento JSON)",
        "analyze": "Analizar",
        "guide_closed": "Guía de categorías ▾",
        "guide_open": "Guía de categorías ▴",
        "placeholder": "El resultado aparecerá aquí.",
        "base_col": "Sin ajuste (base)",
        "ft_col": "Con ajuste",
        "confidence": "confianza",
        "differs": "diferencia",
        "same": "igual",
        "yes": "Sí",
        "no": "No",
        "of_yes": "de «sí»",
        "error": "Error",
        "models_unavailable": "modelos no disponibles",
        "ready": "listo",
        "guide_col_category": "Categoría",
        "guide_col_definition": "Definición",
        "guide_col_domain": "Ámbito de aplicación",
        "guide_col_action": "Acción posterior",
    },
    "hi": {
        "header": "सपोर्ट टिकट ट्राइएज — फाइन-ट्यून किया गया Laya मॉडल",
        "ticket_label": "टिकट (टेक्स्ट या JSON दस्तावेज़)",
        "analyze": "विश्लेषण करें",
        "guide_closed": "श्रेणी गाइड ▾",
        "guide_open": "श्रेणी गाइड ▴",
        "placeholder": "परिणाम यहाँ दिखाई देगा।",
        "base_col": "फाइन-ट्यूनिंग के बिना (बेस)",
        "ft_col": "फाइन-ट्यूनिंग के साथ",
        "confidence": "विश्वास",
        "differs": "अंतर",
        "same": "समान",
        "yes": "हाँ",
        "no": "नहीं",
        "of_yes": "“हाँ” की संभावना",
        "error": "त्रुटि",
        "models_unavailable": "मॉडल उपलब्ध नहीं",
        "ready": "तैयार",
        "guide_col_category": "श्रेणी",
        "guide_col_definition": "परिभाषा",
        "guide_col_domain": "उपयोग का क्षेत्र",
        "guide_col_action": "आगे की कार्रवाई",
    },
}

# Category guide, per language. Question ids match :mod:`layabench.schema`.
# ``choice`` labels are the class names (billing/technical/account, identical in
# every language); ``noul`` labels are the neutral keys "yes"/"no" and ``score``
# labels are the level index, so the page can localise the displayed word while
# the model still reads the original question text.
GUIDE: dict[str, dict[str, dict]] = {
    "en": {
        "department": {
            "title": "Department",
            "question": "Which team should handle this ticket?",
            "categories": [
                {"label": "billing", "definition": "Money and subscriptions: charges, billing errors, invoices, payment methods, plan changes, refunds and credits.", "domain": "Finance / billing operations", "action": "Queue « Invoicing & Billing »"},
                {"label": "technical", "definition": "Product defects and availability: crashes, errors, outages, failed integrations or API calls, sync and data issues.", "domain": "Engineering / SRE", "action": "Queue « Tier-2 Engineering »"},
                {"label": "account", "definition": "Identity and access: login, password reset, two-factor auth, changes to email, username or profile, lockouts.", "domain": "Identity & access management", "action": "Queue « Accounts & Access »"},
            ],
        },
        "urgency": {
            "title": "Urgency",
            "question": "How urgent is this ticket?",
            "categories": [
                {"label": "0", "definition": "Information request or no deadline; a standard reply is fine.", "domain": "No operational impact", "action": "Reply within 2 business days"},
                {"label": "1", "definition": "The customer is inconvenienced or blocked on a task, without critical urgency.", "domain": "Moderate user impact", "action": "Same-day reply"},
                {"label": "2", "definition": "Outage, data or security loss, or a blocking issue with a same-day deadline.", "domain": "High / critical impact", "action": "Immediate handling (on-call)"},
            ],
        },
        "churn_risk": {
            "title": "Churn risk",
            "question": "Does the customer threaten to leave, downgrade or stop paying?",
            "categories": [
                {"label": "yes", "definition": "The text states an intent to leave: «I'm cancelling», «we're switching to a competitor», «fix it or we leave».", "domain": "Customer retention", "action": "Alert the retention team; priority contact."},
                {"label": "no", "definition": "No intent to leave stated in the text.", "domain": "—", "action": "No retention action."},
            ],
        },
        "refund_requested": {
            "title": "Refund requested",
            "question": "Is the customer explicitly asking to be refunded?",
            "categories": [
                {"label": "yes", "definition": "The text asks to get money back: refund, charge reversal, credit or compensation.", "domain": "Billing policy", "action": "Trigger the refund procedure."},
                {"label": "no", "definition": "A complaint about a charge, without a refund request.", "domain": "—", "action": "No refund action."},
            ],
        },
    },
    "fr": {
        "department": {
            "title": "Département",
            "question": "Quelle équipe doit traiter ce ticket ?",
            "categories": [
                {"label": "billing", "definition": "Tout ce qui touche à l'argent : erreurs de facturation, doubles débits, factures, moyens de paiement, changement de plan, remboursements.", "domain": "Finance / facturation", "action": "File « Facturation & encaissement »"},
                {"label": "technical", "definition": "Défauts produit et disponibilité : plantages, erreurs, pannes, échecs d'intégration ou d'API, problèmes de synchronisation.", "domain": "Ingénierie / SRE", "action": "File « Ingénierie niveau 2 »"},
                {"label": "account", "definition": "Identité et accès : connexion, réinitialisation de mot de passe, 2FA, changement d'e-mail ou de profil, comptes bloqués.", "domain": "Gestion des identités et des accès (IAM)", "action": "File « Comptes & accès »"},
            ],
        },
        "urgency": {
            "title": "Urgence",
            "question": "Quel est le degré d'urgence du ticket ?",
            "categories": [
                {"label": "0", "definition": "Demande d'information ou sans échéance : une réponse standard suffit.", "domain": "Aucun impact opérationnel", "action": "Réponse sous 2 jours ouvrés"},
                {"label": "1", "definition": "Le client est gêné ou bloqué sur une tâche, sans urgence critique.", "domain": "Impact utilisateur modéré", "action": "Réponse le jour même"},
                {"label": "2", "definition": "Panne, perte de données ou de sécurité, ou blocage avec échéance le jour même.", "domain": "Impact fort / critique", "action": "Prise en charge immédiate (astreinte)"},
            ],
        },
        "churn_risk": {
            "title": "Risque de départ (churn)",
            "question": "Le client menace-t-il de partir, de rétrograder ou d'arrêter de payer ?",
            "categories": [
                {"label": "yes", "definition": "Le texte exprime une intention de partir : « j'annule », « on passe à la concurrence », « réglez ça ou on part ».", "domain": "Rétention client", "action": "Alerte équipe rétention ; contact prioritaire."},
                {"label": "no", "definition": "Aucune intention de départ exprimée dans le texte.", "domain": "—", "action": "Aucune action de rétention."},
            ],
        },
        "refund_requested": {
            "title": "Demande de remboursement",
            "question": "Le client demande-t-il explicitement à être remboursé ?",
            "categories": [
                {"label": "yes", "definition": "Le texte demande à récupérer de l'argent : remboursement, annulation de débit, avoir, dédommagement.", "domain": "Politique de facturation", "action": "Déclencher la procédure de remboursement."},
                {"label": "no", "definition": "Simple réclamation sur un débit, sans demande de remboursement.", "domain": "—", "action": "Aucune action de remboursement."},
            ],
        },
    },
    "de": {
        "department": {
            "title": "Abteilung",
            "question": "Welches Team soll dieses Ticket bearbeiten?",
            "categories": [
                {"label": "billing", "definition": "Alles rund ums Geld: Fehlbuchungen, Doppelabbuchungen, Rechnungen, Zahlungsmittel, Tarifwechsel, Erstattungen.", "domain": "Finanzen / Abrechnung", "action": "Warteschlange „Rechnung & Zahlung“"},
                {"label": "technical", "definition": "Produktfehler und Verfügbarkeit: Abstürze, Fehler, Ausfälle, fehlgeschlagene Integrationen oder API-Aufrufe, Synchronisierung.", "domain": "Entwicklung / SRE", "action": "Warteschlange „2nd-Level-Technik“"},
                {"label": "account", "definition": "Identität und Zugriff: Anmeldung, Passwort-Reset, Zwei-Faktor-Authentifizierung, Änderung von E-Mail oder Profil, gesperrte Konten.", "domain": "Identity & Access Management", "action": "Warteschlange „Konten & Zugriff“"},
            ],
        },
        "urgency": {
            "title": "Dringlichkeit",
            "question": "Wie dringend ist dieses Ticket?",
            "categories": [
                {"label": "0", "definition": "Informationsanfrage oder ohne Frist: eine Standardantwort genügt.", "domain": "Keine betrieblichen Auswirkungen", "action": "Antwort innerhalb von 2 Werktagen"},
                {"label": "1", "definition": "Der Kunde ist beeinträchtigt oder bei einer Aufgabe blockiert, ohne kritische Dringlichkeit.", "domain": "Mittlere Nutzerauswirkung", "action": "Antwort am selben Tag"},
                {"label": "2", "definition": "Ausfall, Daten- oder Sicherheitsverlust oder Blockade mit Frist am selben Tag.", "domain": "Hohe / kritische Auswirkung", "action": "Sofortige Bearbeitung (Bereitschaft)"},
            ],
        },
        "churn_risk": {
            "title": "Abwanderungsrisiko",
            "question": "Droht der Kunde zu kündigen, herabzustufen oder nicht mehr zu zahlen?",
            "categories": [
                {"label": "yes", "definition": "Der Text drückt Kündigungsabsicht aus: „Ich kündige“, „wir wechseln zur Konkurrenz“, „behebt das oder wir gehen“.", "domain": "Kundenbindung", "action": "Bindungsteam alarmieren; vorrangiger Kontakt."},
                {"label": "no", "definition": "Keine Kündigungsabsicht im Text.", "domain": "—", "action": "Keine Bindungsmaßnahme."},
            ],
        },
        "refund_requested": {
            "title": "Erstattung angefragt",
            "question": "Verlangt der Kunde ausdrücklich eine Erstattung?",
            "categories": [
                {"label": "yes", "definition": "Der Text verlangt Geld zurück: Erstattung, Rückbuchung, Gutschrift oder Entschädigung.", "domain": "Abrechnungsrichtlinie", "action": "Erstattungsverfahren auslösen."},
                {"label": "no", "definition": "Eine Beschwerde über eine Abbuchung, ohne Erstattungsverlangen.", "domain": "—", "action": "Keine Erstattung."},
            ],
        },
    },
    "es": {
        "department": {
            "title": "Departamento",
            "question": "¿Qué equipo debe gestionar este ticket?",
            "categories": [
                {"label": "billing", "definition": "Todo lo relacionado con el dinero: errores de facturación, cobros duplicados, facturas, métodos de pago, cambios de plan, reembolsos.", "domain": "Finanzas / facturación", "action": "Cola «Facturación y cobros»"},
                {"label": "technical", "definition": "Defectos de producto y disponibilidad: cierres inesperados, errores, caídas, fallos de integración o API, problemas de sincronización.", "domain": "Ingeniería / SRE", "action": "Cola «Ingeniería nivel 2»"},
                {"label": "account", "definition": "Identidad y acceso: inicio de sesión, restablecer contraseña, doble factor, cambio de correo o perfil, cuentas bloqueadas.", "domain": "Gestión de identidades y accesos (IAM)", "action": "Cola «Cuentas y accesos»"},
            ],
        },
        "urgency": {
            "title": "Urgencia",
            "question": "¿Qué urgencia tiene este ticket?",
            "categories": [
                {"label": "0", "definition": "Solicitud de información o sin plazo: basta una respuesta estándar.", "domain": "Sin impacto operativo", "action": "Respuesta en 2 días laborables"},
                {"label": "1", "definition": "El cliente está afectado o bloqueado en una tarea, sin urgencia crítica.", "domain": "Impacto moderado en el usuario", "action": "Respuesta el mismo día"},
                {"label": "2", "definition": "Caída, pérdida de datos o de seguridad, o bloqueo con plazo ese mismo día.", "domain": "Impacto alto / crítico", "action": "Atención inmediata (guardia)"},
            ],
        },
        "churn_risk": {
            "title": "Riesgo de baja",
            "question": "¿Amenaza el cliente con irse, bajar de plan o dejar de pagar?",
            "categories": [
                {"label": "yes", "definition": "El texto expresa intención de irse: «me doy de baja», «nos pasamos a la competencia», «arreglen esto o nos vamos».", "domain": "Retención de clientes", "action": "Avisar al equipo de retención; contacto prioritario."},
                {"label": "no", "definition": "No hay intención de irse en el texto.", "domain": "—", "action": "Sin acción de retención."},
            ],
        },
        "refund_requested": {
            "title": "Reembolso solicitado",
            "question": "¿Pide el cliente explícitamente un reembolso?",
            "categories": [
                {"label": "yes", "definition": "El texto pide recuperar dinero: reembolso, anulación del cargo, abono o compensación.", "domain": "Política de facturación", "action": "Activar el procedimiento de reembolso."},
                {"label": "no", "definition": "Una reclamación sobre un cargo, sin pedir reembolso.", "domain": "—", "action": "Sin acción de reembolso."},
            ],
        },
    },
    "hi": {
        "department": {
            "title": "विभाग",
            "question": "इस टिकट को कौन-सी टीम संभाले?",
            "categories": [
                {"label": "billing", "definition": "पैसे से जुड़ी सब बातें: गलत बिलिंग, दोहरा शुल्क, चालान, भुगतान के तरीके, प्लान बदलना, रिफंड।", "domain": "वित्त / बिलिंग", "action": "कतार “बिलिंग और भुगतान”"},
                {"label": "technical", "definition": "उत्पाद दोष और उपलब्धता: क्रैश, त्रुटियाँ, आउटेज, इंटीग्रेशन या API विफलता, सिंक की समस्या।", "domain": "इंजीनियरिंग / SRE", "action": "कतार “लेवल-2 इंजीनियरिंग”"},
                {"label": "account", "definition": "पहचान और पहुँच: लॉगिन, पासवर्ड रीसेट, दो-चरणीय सत्यापन, ईमेल या प्रोफ़ाइल बदलना, खाता लॉक।", "domain": "पहचान एवं पहुँच प्रबंधन (IAM)", "action": "कतार “खाते और पहुँच”"},
            ],
        },
        "urgency": {
            "title": "तात्कालिकता",
            "question": "यह टिकट कितना ज़रूरी है?",
            "categories": [
                {"label": "0", "definition": "जानकारी का अनुरोध या कोई समय-सीमा नहीं: सामान्य उत्तर पर्याप्त है।", "domain": "कोई परिचालन प्रभाव नहीं", "action": "2 कार्यदिवसों में उत्तर"},
                {"label": "1", "definition": "ग्राहक परेशान है या किसी काम में अटका है, पर कोई गंभीर तात्कालिकता नहीं।", "domain": "मध्यम उपयोगकर्ता प्रभाव", "action": "उसी दिन उत्तर"},
                {"label": "2", "definition": "आउटेज, डेटा या सुरक्षा हानि, या उसी दिन की समय-सीमा वाला अवरोध।", "domain": "उच्च / गंभीर प्रभाव", "action": "तत्काल कार्रवाई (ऑन-कॉल)"},
            ],
        },
        "churn_risk": {
            "title": "ग्राहक छोड़ने का जोखिम",
            "question": "क्या ग्राहक छोड़ने, डाउनग्रेड या भुगतान बंद करने की धमकी दे रहा है?",
            "categories": [
                {"label": "yes", "definition": "पाठ में छोड़ने का इरादा है: “मैं रद्द कर रहा हूँ”, “हम प्रतिस्पर्धी के पास जा रहे हैं”।", "domain": "ग्राहक रिटेंशन", "action": "रिटेंशन टीम को सूचित करें; प्राथमिक संपर्क।"},
                {"label": "no", "definition": "पाठ में छोड़ने का कोई इरादा नहीं।", "domain": "—", "action": "कोई रिटेंशन कार्रवाई नहीं।"},
            ],
        },
        "refund_requested": {
            "title": "रिफंड का अनुरोध",
            "question": "क्या ग्राहक स्पष्ट रूप से रिफंड माँग रहा है?",
            "categories": [
                {"label": "yes", "definition": "पाठ में पैसे वापस माँगे गए हैं: रिफंड, शुल्क रद्द करना, क्रेडिट या मुआवज़ा।", "domain": "बिलिंग नीति", "action": "रिफंड प्रक्रिया शुरू करें।"},
                {"label": "no", "definition": "शुल्क पर शिकायत, पर रिफंड का अनुरोध नहीं।", "domain": "—", "action": "कोई रिफंड कार्रवाई नहीं।"},
            ],
        },
    },
}

