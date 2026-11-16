"""Local HTTP server to try a fine-tuned Laya checkpoint from the browser.

    .venv/bin/python tools/serve_model.py --checkpoint checkpoints/t300-softce --device cuda
    # then open http://127.0.0.1:8000

Serves ``tools/tester.html`` at ``/`` and exposes:

* ``GET  /questions`` - the triage policy the model answers
* ``POST /predict``   - body ``{"state": "...", "questions": {...}?}`` -> typed answers
* ``GET  /health``    - liveness + which checkpoint is loaded

Stdlib only (no fastapi/uvicorn). Without ``--checkpoint`` it loads the most
recently written checkpoint directory.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from layabench import i18n  # noqa: E402
from layabench import schema  # noqa: E402

QUESTIONS = schema.questions_for(noul_as_choice=False)
GUIDE = schema.CATEGORY_GUIDE
HTML_FILE = Path(__file__).resolve().parent / "tester.html"
ONEPAGER = ROOT / "laya_onepager.pdf"
MODELS: dict[str, dict] = {}  # model id -> {"agent": <Agent>, "label": <str>}
DEFAULT_MODEL = "ft"


def _lang_of(path: str) -> str:
    """Read ``?lang=`` from a request path, falling back to the default."""
    query = urllib.parse.urlparse(path).query
    lang = urllib.parse.parse_qs(query).get("lang", [i18n.DEFAULT_LANGUAGE])[0]
    return lang if lang in i18n.LANGUAGES else i18n.DEFAULT_LANGUAGE


def newest_checkpoint() -> str | None:
    """Most recently written checkpoint dir that looks loadable."""
    cands = [d for d in (ROOT / "checkpoints").glob("*") if (d / "rl_agent_config.json").exists()]
    if not cands:
        return None
    return str(max(cands, key=lambda d: d.stat().st_mtime))


def normalize(answers: dict) -> dict:
    """Flatten Laya's answers into a small, display-friendly shape."""
    out = {}
    for qid, q in QUESTIONS.items():
        a = answers[qid]
        if q["type"] == "choice":
            out[qid] = {"type": "choice", "label": a["choice"],
                        "confidence": a.get("answer_confidence", a.get("confidence")),
                        "probabilities": a.get("probabilities")}
        elif q["type"] == "score":
            out[qid] = {"type": "score", "score": a["score"], "confidence": a.get("confidence"),
                        "levels": q["criteria"]}
        else:
            p = float(a["noul"])
            out[qid] = {"type": "noul", "yes_prob": p,
                        "confidence": a.get("answer_confidence", max(p, 1.0 - p))}
    return out


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str,
              extra: dict[str, str] | None = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, payload: dict) -> None:
        self._send(code, json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def do_OPTIONS(self) -> None:  # CORS preflight
        self._send(204, b"", "text/plain")

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            if not HTML_FILE.exists():
                self._json(500, {"error": f"missing {HTML_FILE}"})
                return
            self._send(200, HTML_FILE.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/questions":
            self._json(200, {"questions": QUESTIONS})
        elif self.path == "/guide" or self.path.startswith("/guide?"):
            self._json(200, {"guide": i18n.GUIDE[_lang_of(self.path)]})
        elif self.path == "/i18n" or self.path.startswith("/i18n?"):
            lang = _lang_of(self.path)
            self._json(200, {"lang": lang, "default": i18n.DEFAULT_LANGUAGE,
                             "languages": list(i18n.LANGUAGES),
                             "ui": i18n.UI[lang], "guide": i18n.GUIDE[lang]})
        elif self.path == "/models":
            self._json(200, {"models": [{"id": k, "label": v["label"], "name": v.get("name")}
                                        for k, v in MODELS.items()],
                             "default": DEFAULT_MODEL})
        elif self.path in ("/onepager.pdf", "/one-pager.pdf"):
            if not ONEPAGER.exists():
                self._json(404, {"error": "one-pager not generated: run python tools/make_onepager.py"})
                return
            self._send(200, ONEPAGER.read_bytes(), "application/pdf",
                       {"Content-Disposition": 'inline; filename="laya_onepager.pdf"'})
        elif self.path == "/health":
            self._json(200, {"ok": True, "models": list(MODELS), "default": DEFAULT_MODEL})
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/predict":
            self._json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
            state = payload.get("state")
            if not state:
                self._json(400, {"error": "missing 'state'"})
                return
            questions = payload.get("questions") or QUESTIONS
            t0 = time.perf_counter()
            base = MODELS["base"]["agent"].predict(state, questions)
            t1 = time.perf_counter()
            ft = MODELS["ft"]["agent"].predict(state, questions)
            t2 = time.perf_counter()
            self._json(200, {
                "ok": True,
                "latency_ms": {"base": round((t1 - t0) * 1000, 1),
                               "ft": round((t2 - t1) * 1000, 1)},
                "base": normalize(base["answers"]),
                "ft": normalize(ft["answers"]),
            })
        except Exception as exc:  # keep the server alive, report the error
            self._json(500, {"error": f"{type(exc).__name__}: {exc}"})

    def log_message(self, *args) -> None:  # quiet
        pass


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Serve the base and fine-tuned Laya models + tester.html.")
    p.add_argument("--checkpoint", default=None, help="fine-tuned checkpoint dir (default: most recent)")
    p.add_argument("--base-model", default="convaiinnovations/laya", help="base repo")
    p.add_argument("--base-subfolder", default="multilingual", help="base subfolder: english | multilingual")
    p.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    p.add_argument("--port", type=int, default=8000)
    args = p.parse_args(argv)

    import laya

    checkpoint = args.checkpoint or newest_checkpoint()
    if not checkpoint:
        print("no checkpoint found; pass --checkpoint <dir>", file=sys.stderr)
        return 2

    print(f"loading base       {args.base_model}/{args.base_subfolder} (device={args.device}) ...")
    base = laya.load(args.base_model, subfolder=args.base_subfolder, device=args.device)
    MODELS["base"] = {"agent": base, "name": args.base_subfolder,
                      "label": f"Sans fine-tuning ({args.base_subfolder})"}

    print(f"loading fine-tuned {checkpoint} (device={args.device}) ...")
    ft = laya.load(checkpoint, device=args.device)
    MODELS["ft"] = {"agent": ft, "name": Path(checkpoint).name,
                    "label": f"Avec fine-tuning ({Path(checkpoint).name})"}

    # warmups so the first request is fast
    for entry in MODELS.values():
        entry["agent"].predict("warmup", QUESTIONS)

    print(f"serving on http://127.0.0.1:{args.port}  (models: {list(MODELS)})")
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
