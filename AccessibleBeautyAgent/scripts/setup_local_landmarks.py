"""Check or install the pinned local MediaPipe model."""
import argparse
import hashlib
import json
from pathlib import Path
import ssl
from tempfile import NamedTemporaryFile
import urllib.request

import certifi

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'backend/app/vision/face-landmarker.json').read_text(encoding='utf-8'))
    model = ROOT / 'work/models/face_landmarker.task'

    def matches(raw):
        return len(raw) == manifest['bytes'] and hashlib.sha256(raw).hexdigest() == manifest['sha256']

    try:
        if model.is_file() and matches(model.read_bytes()):
            print('本地视觉模型校验通过。')
            return
        if args.check:
            raise ValueError('模型缺失或校验失败。请运行本命令并移除 --check。')
        context = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(manifest['source'], context=context, timeout=30) as response:
            raw = response.read(manifest['bytes'] + 1)
        if not matches(raw):
            raise ValueError('下载文件与锁定校验不一致。')
        model.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(dir=model.parent, delete=False) as temporary:
            path = Path(temporary.name)
            temporary.write(raw)
        try:
            path.replace(model)
        finally:
            path.unlink(missing_ok=True)
        print('本地视觉模型安装并校验通过。')
    except (OSError, ValueError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
