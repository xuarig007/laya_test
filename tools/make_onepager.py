"""Render a one-page PDF presenting Laya, the progressive method and the results.

    python tools/make_onepager.py            # -> laya_onepager.pdf

Uses reportlab (no system dependencies). Verifies the output is exactly one page.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "laya_onepager.pdf"

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph,
                                Spacer, Table, TableStyle)

NAVY = colors.HexColor("#16304f")
BLUE = colors.HexColor("#2f6fb0")
GREY = colors.HexColor("#5b6470")
LIGHT = colors.HexColor("#eef3f8")
LINE = colors.HexColor("#c9d4e0")

ss = getSampleStyleSheet()
TITLE = ParagraphStyle("t", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=20,
                       leading=22, textColor=NAVY, alignment=TA_LEFT, spaceAfter=2)
SUB = ParagraphStyle("s", parent=ss["Normal"], fontName="Helvetica", fontSize=9.3,
                     leading=11.4, textColor=GREY, spaceAfter=8)
H2 = ParagraphStyle("h2", parent=ss["Normal"], fontName="Helvetica-Bold", fontSize=11.8,
                    leading=13.5, textColor=BLUE, spaceBefore=9, spaceAfter=3)
BODY = ParagraphStyle("b", parent=ss["Normal"], fontName="Helvetica", fontSize=9.3,
                      leading=11.6, textColor=colors.HexColor("#20262e"), spaceAfter=3)
BULL = ParagraphStyle("bu", parent=BODY, leftIndent=10, bulletIndent=1, spaceAfter=2.5)
CELL = ParagraphStyle("c", parent=BODY, fontSize=8.4, leading=10.1, spaceAfter=0)
CELLB = ParagraphStyle("cb", parent=CELL, fontName="Helvetica-Bold")
HEAD = ParagraphStyle("hd", parent=CELL, fontName="Helvetica-Bold", textColor=colors.white)
FOOT = ParagraphStyle("f", parent=BODY, fontSize=7.6, leading=9, textColor=GREY)


def p(text, style=BODY):
    return Paragraph(text, style)


def section(num, title):
    return Paragraph(f"{num}&nbsp;&nbsp;{title}", H2)


def table(header, rows, widths, highlight_row=None):
    data = [[Paragraph(h, HEAD) for h in header]]
    for r in rows:
        data.append([c if isinstance(c, Paragraph) else Paragraph(str(c), CELL) for c in r])
    t = Table(data, colWidths=widths, hAlign="LEFT")
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
    ]
    if highlight_row is not None:
        style.append(("BACKGROUND", (0, highlight_row), (-1, highlight_row), colors.HexColor("#dff0e2")))
    t.setStyle(TableStyle(style))
    return t


def build() -> None:
    story = []
    story.append(p("Laya — du zero-shot à la production", TITLE))
    story.append(p("Moteur de décision <b>System 1</b> évalué et fine-tuné sur un cas d'usage support "
                   "multilingue &nbsp;·&nbsp; RTX 4070 (GPU) &nbsp;·&nbsp; <font face='Courier'>laya 0.4.31</font>"
                   " &nbsp;·&nbsp; <font face='Courier'>torch 2.15.0+cu132</font>", SUB))

    story.append(p("Laya est un moteur de décision <b>non-autorégressif</b> : un état (texte, e-mail, ticket ou JSON) "
                   "et des <b>questions typées</b> donnent des réponses typées avec probabilités calibrées en "
                   "<b>un seul forward pass</b> (~18–33 ms), en 100+ langues. Il ne génère jamais de texte — rien à "
                   "parser, rien à halluciner — et un <font face='Courier'>Router</font> choisit le checkpoint selon "
                   "la langue détectée. Licence Apache-2.0, exécution 100 % locale (CPU ou GPU)."))

    story.append(section("1", "Laya en bref"))
    for b in ["<b>3 primitives</b> : <font face='Courier'>choice</font> (choisir), <font face='Courier'>score</font> "
              "(ordonner), <font face='Courier'>noul</font> (probabilité de « oui »).",
              "<b>100+ langues</b>, routage transparent <font face='Courier'>english</font> / "
              "<font face='Courier'>multilingual</font> ; <b>base à spécialiser</b>, pas un moteur zero-shot."]:
        story.append(Paragraph(b, BULL, bulletText="•"))

    story.append(section("2", "Le cas d'usage — passerelle de triage support multilingue"))
    story.append(p("Chaque ticket est transformé en <b>4 décisions typées</b>, en un seul passage :"))
    story.append(table(
        ["question", "type", "sortie", "usage en aval"],
        [["<font face='Courier'>department</font>", "choice", "billing / technical / account", "router vers la bonne file"],
         ["<font face='Courier'>urgency</font>", "score", "0 / 1 / 2", "priorisation / SLA"],
         ["<font face='Courier'>churn_risk</font>", "noul", "P(oui)", "alerte rétention"],
         ["<font face='Courier'>refund_requested</font>", "noul", "P(oui)", "politique de remboursement"]],
        [95, 45, 165, 130]))

    story.append(section("3", "Démarche progressive"))
    story.append(table(
        ["étape", "dispositif", "constat clé"],
        [["<b>1.</b> Benchmark zero-shot", "33 tickets étiquetés, 5 langues, vs baselines (majority, random, règles)",
          "choice 0.91 ; <b>churn_risk 0.60</b> — angle mort, <b>confiant et faux</b>"],
         ["<b>2.</b> Fine-tune (33, CPU)", "complet vs encodeur gelé ; 90 updates",
          "churn reste <b>0.60</b> → le manque est dans les <b>données</b>"],
         ["<b>3.</b> 100 tickets, GPU", "full fine-tune, <font face='Courier'>calib_frac=0.25</font>, 15 époques",
          "choice 0.90, <b>churn 1.00</b> ; la calibration s'ajuste enfin"],
         ["<b>4.</b> Étude 300, formulations inédites", "test par <b>templates tenus à l'écart</b> ; soft-ce vs rlcd ; courbe",
          "choice <b>0.93</b> ; ça <b>généralise</b> (pas de mémorisation)"]],
        [95, 175, 165], highlight_row=4))

    story.append(section("4", "Résultats — test300 : 75 tickets tenus à l'écart, 300 décisions"))
    story.append(table(
        ["run", "choice_acc", "noul_acc", "score_mae ↓", "ece ↓", "brier ↓", "aurc ↓"],
        [["base multilingual", "0.653", "0.753", "0.672", "0.222", "0.237", "0.149"],
         ["<b>FT soft-ce (300)</b>", "<b>0.933</b>", "<b>1.000</b>", "0.098", "<b>0.067</b>", "<b>0.031</b>", "<b>0.004</b>"],
         ["FT rlcd (300)", "0.867", "1.000", "<b>0.075</b>", "0.092", "0.046", "0.008"],
         ["FT soft-ce (65)", "0.720", "1.000", "0.126", "0.072", "0.057", "0.009"]],
        [110, 66, 62, 66, 50, 52, 48], highlight_row=1))

    story.append(Spacer(1, 5))
    story.append(table(
        ["par question — FT soft-ce (300) vs base"],
        [["churn_risk 0.60 → <b>1.00</b> &nbsp;·&nbsp; department 0.65 → <b>0.93</b> &nbsp;·&nbsp; "
          "refund 0.91 → <b>1.00</b> &nbsp;·&nbsp; urgence MAE 0.67 → <b>0.10</b>"]],
        [454]))

    story.append(section("5", "Conclusions"))
    for b in ["<b>La valeur est dans le fine-tuning</b> : choice +0.28, churn 0.60 → <b>1.00</b>, urgence MAE "
              "0.67 → <b>0.10</b>, AURC 0.149 → <b>0.004</b> — et cela tient sur des <b>formulations jamais vues</b>.",
              "<b>soft-ce par défaut</b> (meilleur sur le catégoriel et la calibration) ; <b>rlcd</b> légèrement "
              "meilleur sur l'ordinal.",
              "Les <b>flags binaires</b> s'apprennent avec peu de données ; le <b>choix multi-classe</b> demande du "
              "volume (department 0.72 → 0.93 de 65 à 300 tickets).",
              "<b>Limite</b> : jeu partiellement synthétique ; les valeurs absolues sont optimistes, mais les "
              "<b>comparaisons relatives</b> (loss, taille) sont robustes."]:
        story.append(Paragraph(b, BULL, bulletText="•"))

    story.append(Spacer(1, 3))
    story.append(Paragraph("Reproductible : <font face='Courier'>/appli/laya_test</font> — harness "
                           "<font face='Courier'>layabench run|compare</font>, entraînement "
                           "<font face='Courier'>laya-train</font>, rapports dans <font face='Courier'>results/</font>. "
                           "Documentation : README.md (sections 1–10).", FOOT))

    doc = BaseDocTemplate(str(OUT), pagesize=A4,
                          leftMargin=16 * mm, rightMargin=16 * mm,
                          topMargin=13 * mm, bottomMargin=12 * mm,
                          title="Laya — du zero-shot à la production")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="one", frames=[frame])])
    doc.build(story)

    pages = len(re.findall(rb"/Type\s*/Page[^s]", OUT.read_bytes()))
    print(f"wrote {OUT} ({pages} page(s), {OUT.stat().st_size} bytes)")
    if pages != 1:
        print("WARNING: not exactly one page", file=sys.stderr)


if __name__ == "__main__":
    build()

