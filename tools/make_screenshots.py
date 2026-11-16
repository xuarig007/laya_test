"""Take real screenshots of the web tester (headless Chromium via Playwright).

    .venv/bin/python tools/make_screenshots.py            # server must be running on :9999

For each demo language it selects the language (which switches the whole UI *and*
fills a matching ticket), runs the analysis, and captures the two-column result.
It also captures the open category guide.

    blog/assets/shot-<lang>.png        # the inference result, one per language
    blog/assets/shot-guide-<lang>.png  # the category guide, one per language

Preparation (once)::

    uv pip install --python .venv/bin/python playwright
    .venv/bin/python -m playwright install chromium

Chromium needs a few system libraries. Without root, fetch them locally and the
script will find them automatically::

    mkdir -p /tmp/pwlibs && cd /tmp/pwlibs
    for p in libnspr4 libnss3 libexpat1 libglib2.0-0 libdbus-1-3 libatk1.0-0t64 \\
             libatk-bridge2.0-0t64 libcups2t64 libdrm2 libxkbcommon0 libxcomposite1 \\
             libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 \\
             libasound2t64 libatspi2.0-0t64 libx11-6 libxcb1 libxext6; do
        apt-get download "$p" || true
    done
    mkdir -p root && for d in *.deb; do dpkg-deb -x "$d" root; done
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "blog" / "assets"
URL = "http://127.0.0.1:9999/"
LANGS = ("en", "fr", "de", "es", "hi")

# text of the featured image (title + subtitle, per language)
FEATURED = {
    "en": {
        "kick": "BENCHMARK  &  FINE-TUNING",
        "title": ["Laya, from zero-shot", "to production"],
        "sub": ["An open-source decision engine, benchmarked",
                "and fine-tuned on multilingual ticket triage"],
        "chips": ["5 languages", "33 → 300 tickets", "CPU then GPU"],
    },
    "fr": {
        "kick": "BENCHMARK  &  FINE-TUNING",
        "title": ["Laya, du zero-shot", "à la production"],
        "sub": ["Un moteur de décision open source, évalué",
                "et affiné sur le triage de tickets multilingue"],
        "chips": ["5 langues", "33 → 300 tickets", "CPU puis GPU"],
    },
}

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
NAVY, BLUE, WHITE, GREY, KICK = (22, 48, 79), (47, 111, 176), (255, 255, 255), \
    (201, 216, 232), (127, 176, 224)


def _font(size: int, bold: bool = False):
    from PIL import ImageFont
    return ImageFont.truetype(FONT_B if bold else FONT, size)


def _rounded(im, radius: int):
    from PIL import Image, ImageDraw
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.size[0] - 1, im.size[1] - 1],
                                           radius, fill=255)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    return out


def make_featured(lang: str) -> None:
    """Compose the 2000x1000 featured image: title on the left, UI on the right."""
    from PIL import Image, ImageDraw

    cfg = FEATURED[lang]
    W, H = 2000, 1000

    # the UI panel: crop the two-column result out of the full-page screenshot
    shot = Image.open(OUT / f"shot-{lang}.png").convert("RGB")
    panel = shot.crop((int(0.33 * shot.width), int(0.115 * shot.height),
                       int(0.985 * shot.width), shot.height))
    target_h = 860
    panel = panel.resize((int(panel.width * target_h / panel.height), target_h),
                         Image.LANCZOS)
    panel = _rounded(panel, 18)

    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 16, H], fill=BLUE)
    d.rectangle([panel.width + 70, 70, W, H - 70], outline=(255, 255, 255, 40), width=0)

    # right: the UI, with a light halo so it stands out on the navy background
    x, y = W - panel.width - 70, (H - panel.height) // 2
    halo = Image.new("RGBA", (panel.width + 24, panel.height + 24), (0, 0, 0, 0))
    ImageDraw.Draw(halo).rounded_rectangle([0, 0, halo.width - 1, halo.height - 1],
                                           radius=26, fill=(0, 0, 0, 70))
    img.paste(halo, (x - 12, y - 12), halo)
    img.paste(panel, (x, y), panel)

    # left: title block
    d.text((90, 200), cfg["kick"], font=_font(28, True), fill=KICK)
    d.text((90, 270), cfg["title"][0], font=_font(66, True), fill=WHITE)
    d.text((90, 350), cfg["title"][1], font=_font(66, True), fill=WHITE)
    d.text((92, 480), cfg["sub"][0], font=_font(28), fill=GREY)
    d.text((92, 520), cfg["sub"][1], font=_font(28), fill=GREY)

    cx = 92
    for c in cfg["chips"]:
        f = _font(22, True)
        w = int(d.textlength(c, font=f)) + 40
        d.rounded_rectangle([cx, 620, cx + w, 672], radius=26, outline=BLUE, width=2)
        d.text((cx + 20, 633), c, font=f, fill=KICK)
        cx += w + 14

    d.text((92, 720), "Tickets → department · urgency · churn · refund, in one forward pass",
           font=_font(22), fill=(120, 144, 172))
    out = OUT / f"featured-{lang}.png"
    img.save(out)
    print(f"wrote {out.relative_to(ROOT)}")


def _enable_local_libs() -> None:
    """Point the dynamic loader at locally extracted system libraries, if any."""
    for cand in (ROOT / ".pwlibs" / "usr" / "lib" / "x86_64-linux-gnu",
                 Path("/tmp/pwlibs/root/usr/lib/x86_64-linux-gnu")):
        if cand.is_dir():
            current = os.environ.get("LD_LIBRARY_PATH", "")
            os.environ["LD_LIBRARY_PATH"] = str(cand) + (os.pathsep + current if current else "")
            print(f"using local libraries from {cand}")
            return


def main() -> int:
    _enable_local_libs()
    from playwright.sync_api import sync_playwright

    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1460, "height": 940},
                                device_scale_factor=2)
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector("#langs button", timeout=30000)

        for lang in LANGS:
            page.click(f'#langs button[data-lang="{lang}"]')
            page.wait_for_timeout(400)
            page.click("#go")
            page.wait_for_selector("#out .results", timeout=120000)
            page.wait_for_timeout(600)
            shot = OUT / f"shot-{lang}.png"
            page.screenshot(path=str(shot))
            print(f"wrote {shot.relative_to(ROOT)}")

            # same page with the category guide open (full height)
            page.click("#guideBtn")
            page.wait_for_timeout(400)
            guide = OUT / f"shot-guide-{lang}.png"
            page.screenshot(path=str(guide), full_page=True)
            print(f"wrote {guide.relative_to(ROOT)}")
            page.click("#guideBtn")  # close again
            page.wait_for_timeout(200)

            if lang in FEATURED:
                make_featured(lang)

        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

