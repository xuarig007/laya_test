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
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from layabench import schema  # noqa: E402

QUESTIONS = schema.questions_for(noul_as_choice=False)
GUIDE = schema.CATEGORY_GUIDE
HTML_FILE = Path(__file__).resolve().parent / "tester.html"
AGENT = None
CHECKPOINT = None


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
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
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
        elif self.path == "/guide":
            self._json(200, {"guide": GUIDE})
        elif self.path == "/health":
            self._json(200, {"ok": True, "checkpoint": CHECKPOINT})
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
            result = AGENT.predict(state, questions)
            latency_ms = (time.perf_counter() - t0) * 1000.0
            self._json(200, {"ok": True, "latency_ms": round(latency_ms, 1),
                             "answers": normalize(result["answers"])})
        except Exception as exc:  # keep the server alive, report the error
            self._json(500, {"error": f"{type(exc).__name__}: {exc}"})

    def log_message(self, *args) -> None:  # quiet
        pass


def main(argv: list[str] | None = None) -> int:
    global AGENT, CHECKPOINT
    p = argparse.ArgumentParser(description="Serve a fine-tuned Laya checkpoint + tester.html.")
    p.add_argument("--checkpoint", default=None, help="checkpoint dir (default: most recent)")
    p.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    p.add_argument("--port", type=int, default=8000)
    args = p.parse_args(argv)

    import laya

    CHECKPOINT = args.checkpoint or newest_checkpoint()
    if not CHECKPOINT:
        print("no checkpoint found; pass --checkpoint <dir>", file=sys.stderr)
        return 2
    print(f"loading {CHECKPOINT} (device={args.device}) ...")
    AGENT = laya.load(CHECKPOINT, device=args.device)
    # one warmup so the first request is fast
    AGENT.predict("warmup", QUESTIONS)

    print(f"serving on http://127.0.0.1:{args.port}  (open it in a browser)")
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
