import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import zipfile

import pytest

from scripts import windows_acceptance
from scripts.windows_acceptance import CHECK_NAMES, validate_record


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / 'specs/001-runtime-baseline/windows-acceptance-record.synthetic.json'


def fixture():
    return json.loads(FIXTURE.read_text(encoding='utf-8'))


def real_record():
    record = fixture()
    record['evidence_class'] = 'windows_x64_device'
    record['environment'] = {
        'os': 'Windows', 'architecture': 'AMD64', 'python': '3.12.10',
        'node': 'v26.10.0', 'powershell': '5.1.26100.6899', 'chrome': '156.0.0.0',
        'path_has_non_ascii': True, 'path_has_space': True,
    }
    for name in CHECK_NAMES:
        record['checks'][name] = {'status': 'PASS', 'evidence': f'Synthetic unit-test evidence for {name}.'}
    record['result'] = 'PASS'
    record['limitations'] = 'Synthetic unit test of the validator; not repository evidence.'
    return record


def test_repository_fixture_is_blocked():
    assert validate_record(fixture()) == ('BLOCKED', [])


def test_boolean_schema_version_is_invalid():
    record = fixture()
    record['schema_version'] = True
    status, errors = validate_record(record)
    assert status == 'INVALID'
    assert any('schema_version' in error for error in errors)


def test_preflight_refuses_non_windows_host(monkeypatch):
    monkeypatch.setattr(windows_acceptance.platform, 'system', lambda: 'Darwin')
    with pytest.raises(RuntimeError, match='actual Windows host'):
        windows_acceptance.run_preflight(SimpleNamespace())


def test_structurally_complete_windows_record_can_pass():
    assert validate_record(real_record()) == ('PASS', [])


def test_not_run_keeps_real_record_blocked():
    record = real_record()
    record['checks']['outer_start_entry']['status'] = 'NOT_RUN'
    record['result'] = 'BLOCKED'
    assert validate_record(record) == ('BLOCKED', [])


def test_failure_cannot_be_declared_pass():
    record = real_record()
    record['checks']['directory_move_restart']['status'] = 'FAIL'
    status, errors = validate_record(record)
    assert status == 'INVALID'
    assert 'contradicts' in errors[0]


def test_non_windows_evidence_cannot_claim_device_pass():
    record = real_record()
    record['environment']['os'] = 'Darwin'
    status, errors = validate_record(record)
    assert status == 'INVALID'
    assert any('Windows x64' in error for error in errors)


def test_real_record_requires_chinese_or_other_non_ascii_and_space_path():
    record = real_record()
    record['environment']['path_has_non_ascii'] = False
    status, errors = validate_record(record)
    assert status == 'INVALID'
    assert any('path_case cannot pass' in error for error in errors)


def test_wrong_path_case_can_be_recorded_as_a_real_failure():
    record = real_record()
    record['environment']['path_has_non_ascii'] = False
    record['checks']['path_case'] = {'status': 'FAIL', 'evidence': 'The tested path used ASCII only.'}
    record['result'] = 'FAIL'
    assert validate_record(record) == ('FAIL', [])


def test_user_profile_path_is_rejected():
    record = real_record()
    record['checks']['portable_install']['evidence'] = r'Ran from C:\Users\example\TRACE.'
    status, errors = validate_record(record)
    assert status == 'INVALID'
    assert any('personal' in error for error in errors)


def test_missing_check_is_rejected():
    record = real_record()
    del record['checks']['windows_specific_tests']
    status, errors = validate_record(record)
    assert status == 'INVALID'
    assert any('checks are incomplete' in error for error in errors)


@pytest.mark.parametrize(('field', 'value', 'expected_error'), [
    ('evidence_class', [], 'evidence_class is invalid'),
    ('result', [], 'result is invalid'),
])
def test_malformed_top_level_values_are_invalid_instead_of_crashing(field, value, expected_error):
    record = real_record()
    record[field] = value
    status, errors = validate_record(record)
    assert status == 'INVALID'
    assert expected_error in errors


@pytest.mark.parametrize('value', [
    'PASS',
    {'status': [], 'evidence': 'Malformed status type.'},
    {'status': 'PASS'},
])
def test_malformed_path_check_is_invalid_instead_of_crashing(value):
    record = real_record()
    record['checks']['path_case'] = value
    status, errors = validate_record(record)
    assert status == 'INVALID'
    assert errors


def test_malformed_architecture_is_invalid_instead_of_crashing():
    record = real_record()
    record['environment']['architecture'] = []
    status, errors = validate_record(record)
    assert status == 'INVALID'
    assert 'environment version fields must be non-empty strings' in errors
    assert 'real evidence must identify Windows x64' in errors


def test_windows_wrapper_requires_real_package_path_and_windows_host():
    wrapper = (ROOT / 'AccessibleBeautyAgent/scripts/run_windows_acceptance.ps1').read_text(encoding='utf-8')
    assert '[string]$PackagePath' in wrapper
    assert "Resolve-Path -LiteralPath $PackagePath" in wrapper
    assert "$env:OS -ne 'Windows_NT'" in wrapper


def test_extracted_files_must_match_manifest_hashes(monkeypatch, tmp_path):
    source = tmp_path / 'AccessibleBeautyAgent/README.md'
    source.parent.mkdir()
    source.write_text('public source', encoding='utf-8')
    data = source.read_bytes()
    manifest = {'commit': '1' * 40, 'classification': 'internal verification', 'files': [{
        'path': 'AccessibleBeautyAgent/README.md',
        'size': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
    }]}
    monkeypatch.setattr(windows_acceptance, 'PACKAGE_ROOT', tmp_path)
    assert windows_acceptance.verify_extracted_manifest(manifest) == 1
    source.write_text('tampered source', encoding='utf-8')
    with pytest.raises(ValueError, match='size differs|hash differs'):
        windows_acceptance.verify_extracted_manifest(manifest)


def package_zip(path, commit, content=b'public source', manifest_content=None):
    name = 'AccessibleBeautyAgent/README.md'
    manifest = {
        'commit': commit,
        'classification': 'internal verification',
        'files': [{
            'path': name,
            'size': len(content),
            'sha256': hashlib.sha256(content).hexdigest(),
        }],
    }
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr(name, content)
        archive.writestr(
            'TRACE-BUNDLE-MANIFEST.json',
            json.dumps(manifest_content or manifest),
        )
    return manifest


def test_package_zip_is_bound_to_commit_manifest_and_contents(tmp_path):
    commit = '1' * 40
    path = tmp_path / 'bundle.zip'
    manifest = package_zip(path, commit)
    assert windows_acceptance.verify_package_archive(path, commit) == manifest


def test_package_zip_content_mismatch_is_rejected(tmp_path):
    commit = '1' * 40
    path = tmp_path / 'bundle.zip'
    manifest = package_zip(path, commit)
    manifest['files'][0]['sha256'] = '0' * 64
    path.unlink()
    package_zip(path, commit, manifest_content=manifest)
    with pytest.raises(ValueError, match='hash differs'):
        windows_acceptance.verify_package_archive(path, commit)


def test_package_zip_commit_mismatch_is_rejected(tmp_path):
    path = tmp_path / 'bundle.zip'
    package_zip(path, '1' * 40)
    with pytest.raises(ValueError, match='commit does not match'):
        windows_acceptance.verify_package_archive(path, '2' * 40)


@pytest.mark.parametrize('files', [
    None,
    [{}],
    ['not an object'],
    [{'path': [], 'size': 1, 'sha256': '0' * 64}],
    [{'path': '../outside', 'size': 1, 'sha256': '0' * 64}],
    [{'path': 'file.txt', 'size': -1, 'sha256': '0' * 64}],
    [{'path': 'file.txt', 'size': 1, 'sha256': 'not-a-hash'}],
    [
        {'path': 'file.txt', 'size': 1, 'sha256': '0' * 64},
        {'path': 'file.txt', 'size': 1, 'sha256': '0' * 64},
    ],
])
def test_extracted_manifest_rejects_malformed_rows(files):
    with pytest.raises(ValueError, match='manifest|path|size|SHA-256'):
        windows_acceptance.verify_extracted_manifest({'files': files})
