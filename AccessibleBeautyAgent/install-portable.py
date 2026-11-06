"""Install a movable local TRACE environment using the same path on both platforms."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from runtime import (ROOT, WORK, VENV, ENV_PYTHON, VITE, install_stamp, instance_lock,
                     node_executable, require_python)


def install(force=False):
    require_python()
    node = node_executable()
    npm = Path(node).parent / ('npm.cmd' if os.name == 'nt' else 'npm')
    if not npm.is_file():
        found = shutil.which(npm.name)
        if not found:
            raise RuntimeError('未找到 npm。请使用包含 npm 的 Node.js 安装包。')
        npm = Path(found)
    marker = WORK / 'portable-install.json'
    expected = install_stamp()
    try:
        previous = json.loads(marker.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        previous = None
    if not isinstance(previous, dict):
        previous = None
    if (not force and previous == expected and ENV_PYTHON.is_file()
            and VITE.is_file() and (ROOT / 'frontend/dist/index.html').is_file()):
        print('依赖已安装。', flush=True)
        return
    # A copied virtual environment can contain absolute paths to another directory.
    if VENV.exists() and (previous is None or previous.get('root') != str(ROOT)
                          or previous.get('platform') != sys.platform):
        VENV.rename(VENV.with_name(f'{VENV.name}.previous-{time.time_ns()}'))
    marker.unlink(missing_ok=True)
    if not ENV_PYTHON.is_file():
        subprocess.run([sys.executable, '-m', 'venv', str(VENV)], check=True)
    subprocess.run([str(ENV_PYTHON), '-m', 'pip', 'install', '--only-binary=:all:',
                    '-r', 'backend/requirements-runtime.txt'], cwd=ROOT, check=True)
    subprocess.run([str(ENV_PYTHON), '-m', 'pip', 'check'], cwd=ROOT, check=True)
    npm_cli = npm.parent / 'node_modules/npm/bin/npm-cli.js'
    # Use Node directly on Windows to avoid shell quoting for paths with spaces.
    npm_command = [node, str(npm_cli)] if os.name == 'nt' else [str(npm)]
    for args in (['ci'], ['run', 'build']):
        subprocess.run([*npm_command, *args], cwd=ROOT / 'frontend', check=True)
    temporary = marker.with_suffix('.tmp')
    temporary.write_text(json.dumps(expected, ensure_ascii=False), encoding='utf-8')
    temporary.replace(marker)
    print('安装完成。', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    try:
        WORK.mkdir(exist_ok=True)
        with instance_lock(WORK / 'installer.lock') as acquired:
            if not acquired:
                raise RuntimeError('此目录已有安装正在进行。安装结束后再启动。')
            install(args.force)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f'安装失败。请核对 Python、Node.js 和网络后重试。{error}', file=sys.stderr)
        sys.exit(1)
