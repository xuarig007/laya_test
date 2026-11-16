"""Render every Markdown table of the blog articles as an image, and produce an
import-ready variant where the tables are replaced by images.

    python tools/make_table_images.py

Medium does not render Markdown tables: they collapse into unreadable text
(``runchoicecnoulbefore (base)0.8000.800...``). This script turns each table into
a PNG (``blog/assets/table-<lang>-<n>.png``) and writes
``blog/medium-laya-<lang>.medium.md`` with absolute image URLs — ready to paste
into Medium's "Import a story". Tables that duplicate an image already present
right above them are dropped instead.

The source articles stay untouched (their Markdown tables render fine on GitHub).
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"
ASSETS = BLOG / "assets"
RAW = "https://raw.githubusercontent.com/xuarig007/laya_test/main/blog/assets"

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

NAVY = (22, 48, 79)
WHITE = (255, 255, 255)
LIGHT = (238, 243, 248)
LINE = (201, 212, 224)
GREEN = (223, 240, 226)
DARK = (32, 38, 46)

TARGET_W = 1180
PAD = 28
MIN_COL = 130
LINE_H = 30
VPAD = 13
CELL_FS = 22
HEAD_FS = 22
TITLE_FS = 30


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_B if bold else FONT, size)


def wrap(d: ImageDraw.ImageDraw, text: str, f, max_w: float) -> list[str]:
    """Greedy word-wrap of ``text`` to ``max_w`` pixels."""
    lines, cur = [], ""
    for word in str(text).split():
        trial = f"{cur} {word}".strip()
        if not cur or d.textlength(trial, font=f) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines or [""]


def clean(text) -> str:
    """Drop inline Markdown markup (backticks, emphasis) for rendering."""
    return re.sub(r"[`*]", "", str(text)).strip()


def slug(text: str, lang: str, n: int) -> str:
    """Stable, readable image name derived from the table's title (accents folded)."""
    folded = unicodedata.normalize("NFKD", clean(text)).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", folded.lower()).strip("-")[:48].strip("-")
    return f"table-{lang}-{s}" if s else f"table-{lang}-{n}"


def _bold_cell(text) -> tuple[str, bool]:
    """Return (clean text, is-fully-bold) for one table cell."""
    t = str(text).strip()
    return clean(t), t.startswith("**") and t.endswith("**") and len(t) > 4


def render_table(path: Path, title: str, header: list[str], rows: list[list[str]]) -> None:
    """Draw a table (title + header + rows) and save it as a PNG."""
    meas = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    f_cell, f_bold, f_head = font(CELL_FS), font(CELL_FS, True), font(HEAD_FS, True)
    head = [clean(h) for h in header]
    body = [[_bold_cell(c) for c in row] for row in rows]

    def f_of(bold: bool):
        return f_bold if bold else f_cell

    ncols = len(head)
    natural = [max([meas.textlength(head[j], font=f_head)]
                   + [meas.textlength(body[i][j][0], font=f_of(body[i][j][1]))
                      for i in range(len(body))])
               for j in range(ncols)]
    avail = TARGET_W - 2 * PAD
    widths = [max(MIN_COL, int(n * avail / sum(natural))) for n in natural]
    widths[-1] += avail - sum(widths)  # absorb rounding
    W = 2 * PAD + sum(widths)

    title_h = 74 if title else 0
    hh = max(1, max(len(wrap(meas, h, f_head, widths[j] - 2 * VPAD))
                    for j, h in enumerate(head))) * LINE_H + 2 * VPAD
    row_hs = []
    for row in body:
        cells = [wrap(meas, t, f_of(b), widths[j] - 2 * VPAD) for j, (t, b) in enumerate(row)]
        row_hs.append(max(len(c) for c in cells) * LINE_H + 2 * VPAD)

    img = Image.new("RGB", (W, title_h + hh + sum(row_hs) + PAD + 6), WHITE)
    d = ImageDraw.Draw(img)

    if title:
        d.text((PAD, 26), title, font=font(TITLE_FS, True), fill=NAVY)

    y = title_h
    d.rectangle([PAD, y, W - PAD, y + hh], fill=NAVY)
    x = PAD
    for j, h in enumerate(head):
        d.multiline_text((x + VPAD, y + VPAD), "\n".join(wrap(d, h, f_head, widths[j] - 2 * VPAD)),
                         font=f_head, fill=WHITE, spacing=4)
        x += widths[j]
    y += hh

    for i, row in enumerate(body):
        rh = row_hs[i]
        d.rectangle([PAD, y, W - PAD, y + rh], fill=WHITE if i % 2 == 0 else LIGHT)
        x = PAD
        for j, (t, b) in enumerate(row):
            f = f_of(b)
            d.multiline_text((x + VPAD, y + VPAD), "\n".join(wrap(d, t, f, widths[j] - 2 * VPAD)),
                             font=f, fill=DARK, spacing=4)
            x += widths[j]
        d.line([PAD, y + rh, W - PAD, y + rh], fill=LINE, width=1)
        y += rh

    d.rectangle([PAD, title_h, W - PAD, y], outline=LINE, width=1)
    img.save(path)


SEP = re.compile(r"^\|[\s:|-]+\|$")


def _is_row(line: str) -> bool:
    s = line.strip()
    return s.startswith("|") and s.endswith("|")


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _title_before(lines: list[str], idx: int) -> str:
    """Nearest preceding Markdown heading, cleaned of backticks/asterisks."""
    for k in range(idx - 1, -1, -1):
        s = lines[k].strip()
        if s.startswith("#"):
            return re.sub(r"[`*]", "", s.lstrip("#").strip())
    return ""


def process(lang: str) -> None:
    """Replace every Markdown table of the article with a rendered image.

    The article itself is rewritten (tables -> image links), so ``medium-laya-<lang>.md``
    is directly usable on GitHub *and* importable into Medium.
    """
    path = BLOG / f"medium-laya-{lang}.md"
    lines = path.read_text(encoding="utf-8").splitlines()

    out: list[str] = []
    i, made, dropped = 0, 0, 0
    while i < len(lines):
        line = lines[i]
        if _is_row(line) and i + 1 < len(lines) and SEP.match(lines[i + 1].strip()):
            j = i
            while j < len(lines) and _is_row(lines[j]):
                j += 1
            header = _cells(lines[i])
            rows = [_cells(l) for l in lines[i + 2:j]]

            prev = next((s.strip() for s in reversed(out) if s.strip()), "")
            if prev.startswith("!["):  # an image already shows this table
                print(f"  [{lang}] dropped a table an image already shows: {header}")
                dropped += 1
                i = j
                continue

            title = _title_before(lines, i) or f"{lang} table {made + 1}"
            name = f"{slug(title, lang, made + 1)}.png"
            render_table(ASSETS / name, title, header, rows)
            out.append(f"![{title}]({RAW}/{name})")
            print(f"  [{lang}] {name}  <- {title!r}  ({len(rows)} rows)")
            made += 1
            i = j
            continue
        out.append(line)
        i += 1

    if made or dropped:
        path.write_text(re.sub(r"\n{3,}", "\n\n", "\n".join(out)).rstrip("\n") + "\n",
                        encoding="utf-8")
    print(f"  [{lang}] {path.name}: {made} table(s) -> image(s), {dropped} dropped")


def main() -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)
    print("rendering article tables as images (in place) ...")
    for lang in ("en", "fr"):
        process(lang)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

