"""Build an internal TRACE source verification bundle from a fixed Git commit."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from tempfile import NamedTemporaryFile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
PUBLIC_ASSETS = PurePosixPath('AccessibleBeautyAgent/frontend/public')
PUBLIC_MEDIA = {PUBLIC_ASSETS / name for name in (
    'art/apple-study.jpg', 'models/human.glb', 'visuals/apple-reference.png',
    'visuals/mesh-portrait-preview.png', 'visuals/porcelain-brown-shirt.png',
    'visuals/porcelain-character.png',
)}
LEGACY_STARTUP = PurePosixPath('AccessibleBeautyAgent/docs/旧入口归档')
VOICE_MODELS = PurePosixPath('AccessibleBeautyAgent/voice/models')
MEDIA_EXTENSIONS = {'.aiff', '.avif', '.gif', '.glb', '.heic', '.jpeg', '.jpg', '.m4a',
                    '.mov', '.mp3', '.mp4', '.png', '.wav', '.webm', '.webp'}
PRIVATE_EXTENSIONS = {'.db', '.key', '.onnx', '.p12', '.pem', '.pfx', '.sqlite', '.sqlite3'}
LOCAL_DIRECTORIES = {'node_modules', '__pycache__', 'work', 'dist', '.git',
                     '本次桌面备份说明', '项目资料', '验证与历史说明'}
SECRET_CONTENT = re.compile(
    rb'-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----|'
    rb'(?im:^[ \t]*(?:[A-Z0-9_]*API_KEY|[A-Z0-9_]*ACCESS_TOKEN)\s*=\s*["\x27]?[A-Za-z0-9_-]{24,})'
)
MANIFEST_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def git(*arguments):
    return subprocess.check_output(['git', '-C', str(ROOT), *arguments])


def safe_name(name):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or any(mark in name for mark in ('\\', ':')):
        raise ValueError(f'unsafe archive path: {name}')
    return path


def checked_name(name):
    path = safe_name(name)
    filename = path.name.lower()
    if (any(part in LOCAL_DIRECTORIES or part.startswith('.venv') for part in path.parts)
            or (filename.startswith('.env') and filename != '.env.example')
            or path.suffix.lower() in PRIVATE_EXTENSIONS
            or '.sqlite-' in filename
            or path.is_relative_to('AccessibleBeautyAgent/data/users')
            or path.is_relative_to(VOICE_MODELS)):
        raise ValueError(f'private or local file tracked in release tree: {name}')
    return path


def build(commit, output):
    if output.exists():
        raise FileExistsError(f'archive already exists: {output}')
    commit = git('rev-parse', '--verify', '--end-of-options', f'{commit}^{{commit}}').decode().strip()
    snapshot = git('archive', '--format=zip', commit)
    entries = []
    output.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=output.parent, suffix='.zip', delete=False) as temporary:
        temp_path = Path(temporary.name)
    try:
        with zipfile.ZipFile(io.BytesIO(snapshot)) as source, zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as target:
            for member in source.infolist():
                path = safe_name(member.filename)
                if member.is_dir():
                    continue
                # Model assets may be tracked for local speech, but release bundles intentionally
                # omit the entire tree. Unexpected private files remain hard failures below.
                if path.is_relative_to(VOICE_MODELS):
                    continue
                # These are explicitly local/history trees, not release source. They may exist in
                # the Git snapshot, so omit their files before the stricter private-file checks.
                if any(part in LOCAL_DIRECTORIES or part.startswith('.venv') for part in path.parts):
                    continue
                path = checked_name(member.filename)
                if path.is_relative_to(LEGACY_STARTUP) and path.suffix.lower() in {'.sh','.ps1','.bat','.command'}:
                    continue
                if path.name=='复制文件夹到桌面.command':
                    continue
                if path.as_posix()=='TRACE-BUNDLE-MANIFEST.json':
                    raise ValueError('release tree uses the reserved manifest name')
                if member.external_attr >> 16 & 0o170000 == 0o120000:
                    raise ValueError(f'symlink in release tree: {member.filename}')
                if path.suffix.lower() in MEDIA_EXTENSIONS and path not in PUBLIC_MEDIA:
                    if path.is_relative_to(PUBLIC_ASSETS):
                        raise ValueError(f'public media requires review before inclusion: {member.filename}')
                    continue
                data = source.read(member)
                if SECRET_CONTENT.search(data):
                    raise ValueError(f'possible credential in release tree: {member.filename}')
                target.writestr(member, data)
                entries.append({'path': path.as_posix(), 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
            manifest = zipfile.ZipInfo('TRACE-BUNDLE-MANIFEST.json', MANIFEST_TIMESTAMP)
            manifest.compress_type = zipfile.ZIP_DEFLATED
            manifest.external_attr = 0o100644 << 16
            target.writestr(manifest, json.dumps(
                {'commit': commit, 'classification': 'internal verification', 'files': entries},
                ensure_ascii=False, indent=2,
            ) + '\n')
        with zipfile.ZipFile(temp_path) as archive:
            assert archive.testzip() is None
            assert len(archive.namelist()) == len(entries) + 1
        temp_path.replace(output)
    finally:
        temp_path.unlink(missing_ok=True)
    return commit, len(entries)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--commit', default='HEAD')
    args = parser.parse_args()
    try:
        commit, files = build(args.commit, args.output)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Packaging failed: {error}\n')
    print(f'Internal verification bundle: {commit} ({files} tracked files)')
