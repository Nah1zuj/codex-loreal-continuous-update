#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
command -v node >/dev/null && command -v npm >/dev/null || { echo '请先安装 Node.js 22.12+，再重新打开此入口。'; exit 1; }
node -e 'let [a,b]=process.versions.node.split(".").map(Number);if(a<22||(a===22&&b<12))process.exit(1)' || { echo 'Node.js 至少需要22.12。'; exit 1; }
portable_python=""
for candidate in python3.12 python3.13 python3; do
 if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys;sys.exit(0 if (3,12)<=sys.version_info[:2]<(3,14) else 1)' 2>/dev/null; then portable_python="$candidate"; break; fi
done
[ -n "$portable_python" ] || { echo '请先安装 Python 3.12 或3.13，再重新打开此入口。'; exit 1; }
mkdir -p work
if [ -d .venv-portable ] && [ "$(cat work/install-root.txt 2>/dev/null || true)" != "$PWD" ]; then
 mv .venv-portable ".venv-portable.previous-$(date +%s)"
fi
[ -x .venv-portable/bin/python ] || "$portable_python" -m venv .venv-portable
.venv-portable/bin/python -m pip install -r backend/requirements-windows.txt -r voice/requirements.txt
.venv-portable/bin/python voice/setup_local_voice_models.py
(cd frontend && npm ci && npm run build)
.venv-portable/bin/python -c "import sys;sys.path.insert(0,'voice');from setup_local_voice_models import ready;assert ready(),'本地语音模型不完整，请重新取得完整交付文件夹。'"
printf '%s' "$PWD" > work/install-root.txt
echo '安装完成。以后双击“启动Demo_Mac.command”。'
