"""Check or install pinned official speech assets without processing user audio."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import ssl
import tarfile
from tempfile import TemporaryDirectory
import urllib.request

import certifi

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / 'MODEL-SOURCES.json'


def assets():
    return json.loads(MANIFEST.read_text(encoding='utf-8'))['assets']


def matches(path, record):
    if not path.is_file() or path.stat().st_size != record['bytes']:
        return False
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest() == record['sha256']


def check():
    return [record['file'] for record in assets() if not matches(ROOT / record['file'], record)]


def download():
    missing = {}
    for record in assets():
        if not matches(ROOT / record['file'], record):
            missing.setdefault(record['source'], []).append(record)
    context = ssl.create_default_context(cafile=certifi.where())
    for url, records in missing.items():
        print(f'下载固定版本：{url}', flush=True)
        with TemporaryDirectory(prefix='.model-', dir=ROOT) as scratch:
            directory = Path(scratch)
            archive = directory / 'assets.tar.bz2'
            with urllib.request.urlopen(url, context=context, timeout=60) as response, archive.open('wb') as out:
                shutil.copyfileobj(response, out)
            with tarfile.open(archive) as source:
                entries = source.getmembers()
                for record in records:
                    name = Path(record['file']).name
                    choices = [entry for entry in entries if entry.isfile() and Path(entry.name).name == name]
                    if len(choices) != 1 or choices[0].size != record['bytes']:
                        raise ValueError(f'资源不符合锁定清单：{name}')
                    with source.extractfile(choices[0]) as raw, (directory / name).open('wb') as out:
                        shutil.copyfileobj(raw, out)
                    if not matches(directory / name, record):
                        raise ValueError(f'模型校验失败：{name}')
            for record in records:
                target = ROOT / record['file']
                target.parent.mkdir(parents=True, exist_ok=True)
                (directory / target.name).replace(target)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--download', action='store_true', help='下载缺失或校验失败的固定资源')
    args = parser.parse_args()
    try:
        if args.download:
            download()
        bad = check()
        if bad:
            raise ValueError('文件缺失或校验失败：' + '、'.join(bad) + '。请加 --download 重试。')
    except (OSError, ValueError, tarfile.TarError) as error:
        parser.exit(1, f'{error}\n')
    print('本地语音模型校验通过。')
