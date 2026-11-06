#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
for candidate in python3.12 python3; do
  if command -v "$candidate" >/dev/null && "$candidate" -c 'import sys; sys.exit(sys.version_info[:2] != (3,12))'; then
    exec "$candidate" install-portable.py "$@"
  fi
done
echo '请安装 Python 3.12，然后重新打开此入口。' >&2
exit 1
