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

        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

