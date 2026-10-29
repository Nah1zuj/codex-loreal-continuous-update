#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
VOICE_ENV=.venv-voice
if [ ! -x "$VOICE_ENV/bin/python" ]; then
  VOICE_PYTHON=""
  for candidate in python3.12 python3.13 python3.14 python3; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys;sys.exit(0 if (3,11)<=sys.version_info[:2]<(3,15) else 1)' 2>/dev/null; then VOICE_PYTHON="$candidate"; break; fi
  done
  if [ -z "$VOICE_PYTHON" ]; then echo '本地语音需要 Python 3.12 或 3.13。安装后重新打开启动入口。'; exit 1; fi
  "$VOICE_PYTHON" -m venv "$VOICE_ENV"
fi
if ! "$VOICE_ENV/bin/python" -c 'import sherpa_onnx,fastapi,uvicorn,websockets,certifi,sentencepiece,pypinyin,numpy' >/dev/null 2>&1; then
  "$VOICE_ENV/bin/python" -m pip install -r voice/requirements.txt
fi
if ! "$VOICE_ENV/bin/python" -c "import sys;sys.path.insert(0,'voice');from setup_local_voice_models import ready;sys.exit(0 if ready() else 1)"; then
  "$VOICE_ENV/bin/python" voice/setup_local_voice_models.py
fi
