"""Shared configuration for the local TRACE installer and launcher."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
DEFAULTS = json.loads((ROOT / 'runtime.json').read_text(encoding='utf-8'))
WORK = ROOT / 'work'
VENV = ROOT / '.venv-portable'
ENV_PYTHON = VENV / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
VITE = ROOT / 'frontend/node_modules/vite/bin/vite.js'
INSTALL_INPUTS = (
    'runtime.json', 'backend/requirements-runtime.txt', 'frontend/package-lock.json',
)


def require_python():
    if '.'.join(map(str, sys.version_info[:2])) != DEFAULTS['python']:
        raise RuntimeError(f"请安装 Python {DEFAULTS['python']}.x，再重试。")


def node_executable():
    node = shutil.which('node')
    expected = 'v' + DEFAULTS['node']
    if not node or subprocess.check_output([node, '--version'], text=True).strip() != expected:
        raise RuntimeError(f'请安装 Node.js {expected}，然后重新打开启动窗口。')
    return node


def install_stamp():
    return {
        'root': str(ROOT),
        'platform': sys.platform,
        'python': DEFAULTS['python'],
        'inputs': {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
                   for path in INSTALL_INPUTS},
    }


def isolated_environment(directory):
    """Configure an isolated database and disable dotenv and remote services."""
    return {
        'TRACE_ENV_FILE': os.devnull,
        'MEMORY_PATH': str(directory / 'beauty.sqlite'),
        'MODEL_PROVIDER': 'mock',
        'REFERENCE_PROVIDER': 'mock',
        'VISION_PROVIDER': 'mock',
        'EMBEDDING_PROVIDER': 'mock',
        'RERANKER_PROVIDER': 'mock',
        'READING_PROVIDER': 'mock',
        'ALLOW_REMOTE_AI': 'false',
        'DASHSCOPE_API_KEY': '',
        'DEEPSEEK_API_KEY': '',
        'COMPATIBLE_API_KEY': '',
        'RESEARCH_MODE': 'false',
        'DEVELOPER_MODE': 'true',
        'ADMIN_ENABLED': 'true',
        'VOICE_PROVIDER': 'browser',
    }



@contextmanager
def instance_lock(path):
    with path.open('a+b') as lock:
        lock.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            yield False
        else:
            yield True
