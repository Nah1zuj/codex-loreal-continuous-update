#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/AccessibleBeautyAgent"
if [ ! -x .venv-portable/bin/python ] || [ "$(cat work/install-root.txt 2>/dev/null || true)" != "$PWD" ] || [ ! -f frontend/node_modules/vite/bin/vite.js ]; then
 ./install-portable.sh || { read -r -p '首次安装失败，按回车关闭。' _; exit 1; }
fi
if .venv-portable/bin/python launch-portable.py; then
 exit 0
else
 result=$?
 read -r -p '启动失败，请保留错误信息；按回车关闭。' _
 exit "$result"
fi
