"""Generate the images for a Medium article: cover + results table.

    python tools/make_medium_assets.py     # -> blog/assets/cover.png, results.png

Medium renders images but not Markdown tables, so the key comparison is shipped
as a picture. Pillow + DejaVu fonts, no extra dependency.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "blog" / "assets"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

NAVY = (22, 48, 79)
BLUE = (47, 111, 176)
KICK = (127, 176, 224)
WHITE = (255, 255, 255)
GREY = (201, 216, 232)
LIGHT = (238, 243, 248)
LINE = (201, 212, 224)
GREEN = (223, 240, 226)
DARK = (32, 38, 46)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_B if bold else FONT, size)


COVER = {
    "fr": {
        "kick": "BENCHMARK  &  FINE-TUNING",
        "title": ["Laya, du zero-shot", "à la production"],
        "sub": ["Un moteur de décision open source évalué et affiné",
                "sur un cas d'usage réel : le triage de tickets support"],
        "chips": ["5 langues", "33 → 300 tickets", "CPU puis GPU", "soft-ce vs rlcd"],
    },
    "en": {
        "kick": "BENCHMARK  &  FINE-TUNING",
        "title": ["Laya, from zero-shot", "to production"],
        "sub": ["An open-source decision engine benchmarked and fine-tuned",
                "on a real use case: multilingual support-ticket routing"],
        "chips": ["5 languages", "33 → 300 tickets", "CPU then GPU", "soft-ce vs rlcd"],
    },
}
FOOT = "convaiinnovations/laya  ·  torch 2.15  ·  RTX 4070"

RESULTS = {
    "fr": {
        "title": "Triage de tickets — test tenu à l'écart (300 décisions)",
        "sub": "formulations jamais vues à l'entraînement  ·  ↓ = plus bas est meilleur",
        "cols": [("Modèle", 430, "l"), ("choice_acc", 210, "c"), ("noul_acc", 200, "c"),
                 ("score_mae ↓", 230, "c"), ("ECE ↓", 180, "c"), ("AURC ↓", 180, "c")],
        "rows": [("base multilingual", "0.653", "0.753", "0.672", "0.222", "0.149", None),
                 ("FT soft-ce (300 tickets)", "0.933", "1.000", "0.098", "0.067", "0.004", "best"),
                 ("FT rlcd (300 tickets)", "0.867", "1.000", "0.075", "0.092", "0.008", None),
                 ("FT soft-ce (65 tickets)", "0.720", "1.000", "0.126", "0.072", "0.009", None)],
    },
    "en": {
        "title": "Ticket triage — held-out test (300 decisions)",
        "sub": "phrasings never seen during training  ·  ↓ = lower is better",
        "cols": [("Model", 430, "l"), ("choice_acc", 210, "c"), ("noul_acc", 200, "c"),
                 ("score_mae ↓", 230, "c"), ("ECE ↓", 180, "c"), ("AURC ↓", 180, "c")],
        "rows": [("base multilingual", "0.653", "0.753", "0.672", "0.222", "0.149", None),
                 ("FT soft-ce (300 tickets)", "0.933", "1.000", "0.098", "0.067", "0.004", "best"),
                 ("FT rlcd (300 tickets)", "0.867", "1.000", "0.075", "0.092", "0.008", None),
                 ("FT soft-ce (65 tickets)", "0.720", "1.000", "0.126", "0.072", "0.009", None)],
    },
}


def _center(d: ImageDraw.ImageDraw, cx: int, y: int, text: str, f, fill) -> None:
    w = d.textbbox((0, 0), text, font=f)[2]
    d.text((cx - w / 2, y), text, font=f, fill=fill)


def cover(path: Path, lang: str) -> None:
    cfg = COVER[lang]
    W, H = 1500, 750
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 16, H], fill=BLUE)

    d.text((90, 140), cfg["kick"], font=font(27, True), fill=KICK)
    d.text((90, 220), cfg["title"][0], font=font(76, True), fill=WHITE)
    d.text((90, 315), cfg["title"][1], font=font(76, True), fill=WHITE)
    d.text((92, 450), cfg["sub"][0], font=font(31), fill=GREY)
    d.text((92, 492), cfg["sub"][1], font=font(31), fill=GREY)

    x = 92
    for c in cfg["chips"]:
        f = font(23, True)
        w = d.textbbox((0, 0), c, font=f)[2] + 44
        d.rounded_rectangle([x, 610, x + w, 668], radius=29, outline=BLUE, width=2)
        _center(d, x + w // 2, 625, c, f, KICK)
        x += w + 16

    d.text((92, 700), FOOT, font=font(21), fill=(110, 132, 160))
    img.save(path)


def results(path: Path, lang: str) -> None:
    cfg = RESULTS[lang]
    cols = cfg["cols"]
    rows = cfg["rows"]
    pad, rh, hh = 40, 62, 66
    W = 2 * pad + sum(c[1] for c in cols)
    title_h = 130
    H = title_h + hh + rh * len(rows) + pad
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    d.text((pad, 34), cfg["title"], font=font(30, True), fill=NAVY)
    d.text((pad, 78), cfg["sub"], font=font(22), fill=(110, 120, 135))

    y = title_h
    d.rectangle([pad, y, W - pad, y + hh], fill=NAVY)
    x = pad
    for name, w, align in cols:
        f = font(23, True)
        if align == "l":
            d.text((x + 18, y + 20), name, font=f, fill=WHITE)
        else:
            cw = d.textbbox((0, 0), name, font=f)[2]
            d.text((x + (w - cw) / 2, y + 20), name, font=f, fill=WHITE)
        x += w

    for i, row in enumerate(rows):
        y = title_h + hh + i * rh
        best = row[-1] == "best"
        d.rectangle([pad, y, W - pad, y + rh],
                    fill=GREEN if best else (WHITE if i % 2 == 0 else LIGHT))
        d.line([pad, y + rh, W - pad, y + rh], fill=LINE, width=1)
        x = pad
        for (name, w, align), val in zip(cols, row[:6]):
            f = font(23, True) if (align == "l" or best) else font(23)
            fill = NAVY if align == "l" else DARK
            if align == "l":
                d.text((x + 18, y + 19), val, font=f, fill=fill)
            else:
                cw = d.textbbox((0, 0), val, font=f)[2]
                d.text((x + (w - cw) / 2, y + 19), val, font=f, fill=fill)
            x += w
    d.rectangle([pad, title_h, W - pad, H - pad], outline=LINE, width=1)
    img.save(path)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for lang in ("fr", "en"):
        cover(OUT / f"cover-{lang}.png", lang)
        results(OUT / f"results-{lang}.png", lang)
    for old in ("cover.png", "results.png"):  # drop the first, unsuffixed versions
        p = OUT / old
        if p.exists():
            p.unlink()
    for p in sorted(OUT.glob("*.png")):
        print(f"wrote {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
