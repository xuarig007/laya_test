#!/usr/bin/env bash
# Start (or restart) the local tester server for the fine-tuned model.
#
#   bash tools/serve.sh                          # device=cuda, port=9999
#   PORT=8000 DEVICE=cpu bash tools/serve.sh     # override via env vars
#   bash tools/serve.sh --checkpoint checkpoints/t300-softce --port 9999
#
# Extra arguments are forwarded to tools/serve_model.py.
# Stop it with: pkill -f tools/serve_model.py
set -euo pipefail
cd "$(dirname "$0")/.."

DEVICE="${DEVICE:-cuda}"
PORT="${PORT:-9999}"
PY=".venv/bin/python"

if [ ! -x "$PY" ]; then
    echo "error: $PY not found. Create it with:" >&2
    echo "  uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python laya" >&2
    exit 1
fi

# stop a previous instance if any
if pkill -f "tools/serve_model.py" 2>/dev/null; then
    echo "stopped previous instance"
    sleep 1
fi

echo "starting server  (device=$DEVICE, port=$PORT)"
echo "open:  http://127.0.0.1:$PORT"
exec "$PY" tools/serve_model.py --device "$DEVICE" --port "$PORT" "$@"
