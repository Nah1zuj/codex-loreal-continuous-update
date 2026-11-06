#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
NO_BROWSER=0
for arg in "$@"; do
  case "$arg" in --no-browser) NO_BROWSER=1;; *) echo "Unknown option: $arg" >&2; exit 1;; esac
done
for tool in node curl lsof; do command -v "$tool" >/dev/null || { echo "Missing tool: $tool" >&2; exit 1; }; done
if [ ! -x .venv/bin/python ] || [ ! -f frontend/node_modules/vite/bin/vite.js ]; then
  echo "Install dependencies first. See 01_Mac安装与启动说明.txt." >&2
  exit 1
fi
./setup-voice-mac.sh
for port in 8002 5174 8003; do
  if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Port $port is in use. No existing process was stopped." >&2
    exit 1
  fi
done
mkdir -p work
export MPLCONFIGDIR="$PWD/work/matplotlib"
mkdir -p "$MPLCONFIGDIR"
BACKEND_PID=""
FRONTEND_PID=""
VOICE_PID=""
cleanup() {
  for owned_pid in "$BACKEND_PID" "$FRONTEND_PID" "$VOICE_PID"; do
    if [ -n "$owned_pid" ] && kill -0 "$owned_pid" 2>/dev/null; then
      kill "$owned_pid" 2>/dev/null || true
    fi
  done
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8002 >work/mac-backend.log 2>&1 &
BACKEND_PID=$!
.venv-voice/bin/python -m uvicorn server:app --app-dir voice --host 127.0.0.1 --port 8003 >work/local-voice.log 2>&1 &
VOICE_PID=$!
(cd frontend && exec node node_modules/vite/bin/vite.js --config vite.package.config.ts) >work/mac-frontend.log 2>&1 &
FRONTEND_PID=$!
READY=0
for _ in $(seq 1 120); do
  if ! kill -0 "$BACKEND_PID" 2>/dev/null || ! kill -0 "$FRONTEND_PID" 2>/dev/null || ! kill -0 "$VOICE_PID" 2>/dev/null; then
    echo "A server exited. See work/mac-backend.log and work/mac-frontend.log." >&2
    exit 1
  fi
  health=$(curl -fsS --max-time 1 http://127.0.0.1:8002/api/health 2>/dev/null || true)
  front_code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 1 http://127.0.0.1:5174/ 2>/dev/null || true)
  voice_health=$(curl -fsS --max-time 1 http://127.0.0.1:8003/voice/health 2>/dev/null || true)
  if [[ "$voice_health" == *'"ready":true'* ]] && [[ "$health" == *'"status":"ok"'* ]] && [ "$front_code" = 200 ]; then READY=1; break; fi
  sleep 0.5
done
if [ "$READY" -ne 1 ]; then echo "Startup timed out. See work/mac-*.log." >&2; exit 1; fi
echo "TRACE V5 correct version: http://127.0.0.1:5174/"
echo "Backend: http://127.0.0.1:8002/api/health"
echo "Keep this terminal open. Control+C stops only this launcher's three services."
if [ "$NO_BROWSER" -eq 0 ]; then open http://127.0.0.1:5174/ || true; fi
while kill -0 "$BACKEND_PID" 2>/dev/null && kill -0 "$FRONTEND_PID" 2>/dev/null && kill -0 "$VOICE_PID" 2>/dev/null; do sleep 1; done
echo "A service stopped. See work/mac-*.log." >&2
exit 1
