import io
import json
import zipfile

import pytest

from scripts import pack_source


COMMIT = '1' * 40


def snapshot(*entries):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        for name, data in entries:
            archive.writestr(name, data)
    return buffer.getvalue()


def fake_git(archive):
    def run(*arguments):
        if arguments[0] == 'rev-parse':
            return (COMMIT + '\n').encode()
        if arguments[0] == 'archive':
            return archive
        raise AssertionError(arguments)
    return run


def test_pack_excludes_tracked_voice_model_tree(monkeypatch, tmp_path):
    source = snapshot(
        ('AccessibleBeautyAgent/voice/models/', b''),
        ('AccessibleBeautyAgent/voice/models/asr/model.int8.onnx', b'private model'),
        ('AccessibleBeautyAgent/voice/models/asr/tokens.txt', b'private tokens'),
        ('本次桌面备份说明/备份说明.txt', b'local history'),
        ('项目资料/research.pdf', b'non-release research'),
        ('AccessibleBeautyAgent/work/runtime.log', b'local runtime'),
        ('AccessibleBeautyAgent/README.md', b'public source'),
    )
    monkeypatch.setattr(pack_source, 'git', fake_git(source))
    output = tmp_path / 'bundle.zip'
    commit, files = pack_source.build('HEAD', output)
    assert (commit, files) == (COMMIT, 1)
    with zipfile.ZipFile(output) as archive:
        assert archive.namelist() == ['AccessibleBeautyAgent/README.md', 'TRACE-BUNDLE-MANIFEST.json']
        manifest = json.loads(archive.read('TRACE-BUNDLE-MANIFEST.json'))
    assert manifest['commit'] == COMMIT
    assert [row['path'] for row in manifest['files']] == ['AccessibleBeautyAgent/README.md']


def test_pack_still_rejects_accidental_private_files(monkeypatch, tmp_path):
    source = snapshot(
        ('AccessibleBeautyAgent/README.md', b'public source'),
        ('AccessibleBeautyAgent/data/users/private.sqlite', b'private data'),
    )
    monkeypatch.setattr(pack_source, 'git', fake_git(source))
    with pytest.raises(ValueError, match='private or local file tracked'):
        pack_source.build('HEAD', tmp_path / 'bundle.zip')
