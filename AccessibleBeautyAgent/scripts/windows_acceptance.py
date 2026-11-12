"""Run or validate the Windows x64 runtime acceptance preflight."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT.parent
CHECK_NAMES = {
    'manifest_commit', 'manifest_files', 'package_sha256', 'path_case',
    'clean_package_without_voice_models',
    'portable_install', 'missing_voice_runtime', 'model_install_runtime',
    'occupied_port_preserved', 'duplicate_start_preserved', 'owned_ports_released',
    'outer_install_entry', 'outer_start_entry', 'directory_move_restart',
    'windows_specific_tests',
}
STATUSES = {'PASS', 'FAIL', 'NOT_RUN'}
TOP_LEVEL_KEYS = {
    'schema_version', 'record_kind', 'evidence_class', 'expected_commit',
    'package_sha256', 'environment', 'checks', 'result', 'limitations',
}
ENVIRONMENT_KEYS = {
    'os', 'architecture', 'python', 'node', 'powershell', 'chrome',
    'path_has_non_ascii', 'path_has_space',
}
EMAIL = re.compile(r'(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b')
CN_MOBILE = re.compile(r'(?<!\d)1[3-9]\d{9}(?!\d)')
WINDOWS_USER_PATH = re.compile(r'(?i)[A-Z]:\\Users\\[^\\\s]+')


def blank_check(evidence):
    return {'status': 'NOT_RUN', 'evidence': evidence}


def text_values(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from text_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from text_values(item)


def validate_record(record):
    errors = []
    if not isinstance(record, dict):
        return 'INVALID', ['record must be a JSON object']
    if set(record) != TOP_LEVEL_KEYS:
        errors.append('top-level fields are incomplete or unexpected')
        return 'INVALID', errors
    if (type(record['schema_version']) is not int or record['schema_version'] != 1
            or record['record_kind'] != 'windows_runtime_acceptance'):
        errors.append('schema_version or record_kind is invalid')
    evidence_class = record['evidence_class']
    if not isinstance(evidence_class, str) or evidence_class not in {'windows_x64_device', 'synthetic_fixture'}:
        errors.append('evidence_class is invalid')
    if not isinstance(record['expected_commit'], str) or not re.fullmatch(r'[0-9a-f]{40}', record['expected_commit']):
        errors.append('expected_commit must be a full lowercase Git SHA')
    if not isinstance(record['package_sha256'], str) or not re.fullmatch(r'[0-9a-f]{64}', record['package_sha256']):
        errors.append('package_sha256 must be a lowercase SHA-256')

    environment = record['environment']
    if not isinstance(environment, dict) or set(environment) != ENVIRONMENT_KEYS:
        errors.append('environment fields are incomplete or unexpected')
        environment = {}
    else:
        string_keys = ENVIRONMENT_KEYS - {'path_has_non_ascii', 'path_has_space'}
        if any(not isinstance(environment[key], str) or not environment[key].strip() for key in string_keys):
            errors.append('environment version fields must be non-empty strings')
        if any(type(environment[key]) is not bool for key in ('path_has_non_ascii', 'path_has_space')):
            errors.append('path flags must be booleans')
        if evidence_class == 'windows_x64_device':
            if (not isinstance(environment['os'], str)
                    or environment['os'] != 'Windows'
                    or not isinstance(environment['architecture'], str)
                    or environment['architecture'].lower() not in {'amd64', 'x86_64'}):
                errors.append('real evidence must identify Windows x64')

    checks = record['checks']
    if not isinstance(checks, dict) or set(checks) != CHECK_NAMES:
        errors.append('checks are incomplete or unexpected')
        checks = {}
    else:
        for name, check in checks.items():
            if not isinstance(check, dict) or set(check) != {'status', 'evidence'}:
                errors.append(f'{name} fields are incomplete or unexpected')
                continue
            if not isinstance(check['status'], str) or check['status'] not in STATUSES:
                errors.append(f'{name} status is invalid')
            if not isinstance(check['evidence'], str) or not check['evidence'].strip():
                errors.append(f'{name} evidence must be a non-empty string')
        path_case = checks.get('path_case')
        if (isinstance(path_case, dict)
                and path_case.get('status') == 'PASS'
                and (not environment.get('path_has_non_ascii') or not environment.get('path_has_space'))):
            errors.append('path_case cannot pass without non-ASCII text and a space')

    if not isinstance(record['result'], str) or record['result'] not in {'PASS', 'FAIL', 'BLOCKED'}:
        errors.append('result is invalid')
    if not isinstance(record['limitations'], str) or not record['limitations'].strip():
        errors.append('limitations must be a non-empty string')
    for value in text_values(record):
        if EMAIL.search(value) or CN_MOBILE.search(value) or WINDOWS_USER_PATH.search(value):
            errors.append('record contains apparent personal contact or user-path information')
            break
    if errors:
        return 'INVALID', errors

    statuses = {check['status'] for check in checks.values()}
    if 'FAIL' in statuses:
        derived = 'FAIL'
    elif evidence_class != 'windows_x64_device' or 'NOT_RUN' in statuses:
        derived = 'BLOCKED'
    else:
        derived = 'PASS'
    if record['result'] != derived:
        return 'INVALID', [f'declared result {record["result"]} contradicts derived result {derived}']
    return derived, []


def load_record(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def models_valid():
    manifest = json.loads((ROOT / 'voice/MODEL-SOURCES.json').read_text(encoding='utf-8'))
    for item in manifest['assets']:
        path = ROOT / 'voice' / item['file']
        if not path.is_file() or path.stat().st_size != item['bytes']:
            return False
        with path.open('rb') as source:
            if hashlib.file_digest(source, 'sha256').hexdigest() != item['sha256']:
                return False
    return True


def validated_manifest_files(manifest):
    if (not isinstance(manifest, dict)
            or set(manifest) != {'commit', 'classification', 'files'}
            or not isinstance(manifest.get('commit'), str)
            or not re.fullmatch(r'[0-9a-f]{40}', manifest['commit'])
            or manifest.get('classification') != 'internal verification'
            or not isinstance(manifest.get('files'), list)
            or not manifest['files']):
        raise ValueError('Bundle manifest file list must be a non-empty array.')
    expected = {}
    for index, item in enumerate(manifest['files']):
        if not isinstance(item, dict) or set(item) != {'path', 'size', 'sha256'}:
            raise ValueError(f'Bundle manifest row {index} is incomplete or unexpected.')
        name = item['path']
        path = PurePosixPath(name) if isinstance(name, str) else None
        if (path is None or not name or path.is_absolute() or '..' in path.parts
                or any(mark in name for mark in ('\\', ':'))):
            raise ValueError(f'Bundle manifest row {index} has an unsafe path.')
        if type(item['size']) is not int or item['size'] < 0:
            raise ValueError(f'Bundle manifest row {index} has an invalid size.')
        if (not isinstance(item['sha256'], str)
                or not re.fullmatch(r'[0-9a-f]{64}', item['sha256'])):
            raise ValueError(f'Bundle manifest row {index} has an invalid SHA-256.')
        if name in expected:
            raise ValueError(f'Bundle manifest contains a duplicate path: {name}')
        expected[name] = item
    return expected


def verify_package_archive(package_path, expected_commit):
    try:
        with zipfile.ZipFile(package_path) as archive:
            corrupt = archive.testzip()
            if corrupt is not None:
                raise ValueError(f'Package ZIP contains a corrupt entry: {corrupt}')
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise ValueError('Package ZIP contains duplicate entry names.')
            if names.count('TRACE-BUNDLE-MANIFEST.json') != 1:
                raise ValueError('Package ZIP must contain exactly one bundle manifest.')
            manifest = json.loads(archive.read('TRACE-BUNDLE-MANIFEST.json'))
            expected = validated_manifest_files(manifest)
            if manifest['commit'] != expected_commit:
                raise ValueError('Package ZIP manifest commit does not match ExpectedCommit.')
            if set(names) != set(expected) | {'TRACE-BUNDLE-MANIFEST.json'}:
                raise ValueError('Package ZIP entries do not exactly match its manifest.')
            for name, item in expected.items():
                data = archive.read(name)
                if len(data) != item['size']:
                    raise ValueError(f'Package ZIP file size differs from manifest: {name}')
                if hashlib.sha256(data).hexdigest() != item['sha256']:
                    raise ValueError(f'Package ZIP file hash differs from manifest: {name}')
    except (zipfile.BadZipFile, KeyError, json.JSONDecodeError) as error:
        raise ValueError(f'Package ZIP or manifest is invalid: {error}') from error
    return manifest


def verify_extracted_manifest(manifest):
    expected = validated_manifest_files(manifest)
    actual = {
        path.relative_to(PACKAGE_ROOT).as_posix()
        for path in PACKAGE_ROOT.rglob('*')
        if path.is_file() and path.name != 'TRACE-BUNDLE-MANIFEST.json'
    }
    if actual != set(expected):
        raise ValueError('Extracted files do not exactly match the bundle manifest.')
    for name, item in expected.items():
        path = PACKAGE_ROOT / name
        if path.stat().st_size != item['size']:
            raise ValueError(f'Extracted file size differs from manifest: {name}')
        with path.open('rb') as source:
            if hashlib.file_digest(source, 'sha256').hexdigest() != item['sha256']:
                raise ValueError(f'Extracted file hash differs from manifest: {name}')
    return len(expected)


def command_ok(command):
    completed = subprocess.run(command, cwd=ROOT)
    return completed.returncode == 0


def set_check(record, name, status, evidence):
    record['checks'][name] = {'status': status, 'evidence': evidence}


def write_record(record, directory):
    statuses = {check['status'] for check in record['checks'].values()}
    record['result'] = 'FAIL' if 'FAIL' in statuses else 'BLOCKED' if 'NOT_RUN' in statuses else 'PASS'
    directory.mkdir(parents=True, exist_ok=False)
    path = directory / 'windows-acceptance.json'
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return path


def run_preflight(args):
    if os.name != 'nt' or platform.system() != 'Windows':
        raise RuntimeError('Windows acceptance preflight must run on an actual Windows host.')
    architecture = platform.machine()
    if architecture.lower() not in {'amd64', 'x86_64'}:
        raise RuntimeError(f'Windows x64 is required; detected {architecture}.')
    root_text = str(ROOT)
    path_has_non_ascii = any(ord(character) > 127 for character in root_text)
    path_has_space = any(character.isspace() for character in root_text)
    node = subprocess.check_output(['node', '--version'], text=True).strip()
    checks = {name: blank_check('Not reached in this run.') for name in CHECK_NAMES}
    record = {
        'schema_version': 1,
        'record_kind': 'windows_runtime_acceptance',
        'evidence_class': 'windows_x64_device',
        'expected_commit': args.expected_commit,
        'package_sha256': args.package_sha256,
        'environment': {
            'os': 'Windows', 'architecture': architecture,
            'python': platform.python_version(), 'node': node,
            'powershell': args.powershell_version, 'chrome': args.chrome_version,
            'path_has_non_ascii': path_has_non_ascii, 'path_has_space': path_has_space,
        },
        'checks': checks,
        'result': 'BLOCKED',
        'limitations': 'Automated preflight cannot prove double-click entries or directory-move recovery; complete the manual packet.',
    }
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output = ROOT / 'work/windows-acceptance' / timestamp
    failed = False
    current_check = 'package_sha256'
    try:
        if not re.fullmatch(r'[0-9a-f]{40}', args.expected_commit):
            raise ValueError('Expected commit must be a full lowercase Git SHA.')
        if not re.fullmatch(r'[0-9a-f]{64}', args.package_sha256):
            raise ValueError('Package SHA-256 must contain 64 lowercase hexadecimal characters.')
        package_path = args.package_path.resolve(strict=True)
        with package_path.open('rb') as source:
            actual_package_sha256 = hashlib.file_digest(source, 'sha256').hexdigest()
        if actual_package_sha256 != args.package_sha256:
            raise ValueError('Source ZIP SHA-256 does not match PackageSha256.')
        set_check(record, 'package_sha256', 'PASS', 'The supplied source ZIP hash matches PackageSha256.')
        current_check = 'manifest_commit'
        manifest = verify_package_archive(package_path, args.expected_commit)
        extracted_manifest = json.loads(
            (PACKAGE_ROOT / 'TRACE-BUNDLE-MANIFEST.json').read_text(encoding='utf-8')
        )
        if extracted_manifest != manifest:
            raise ValueError('Extracted bundle manifest differs from the supplied PackagePath ZIP.')
        set_check(record, 'manifest_commit', 'PASS', 'Bundle manifest commit matches ExpectedCommit.')
        current_check = 'manifest_files'
        file_count = verify_extracted_manifest(manifest)
        set_check(record, 'manifest_files', 'PASS', f'All {file_count} extracted files match manifest size and SHA-256.')
        current_check = 'path_case'
        if not path_has_non_ascii or not path_has_space:
            raise ValueError('Extract the package to a path containing non-ASCII text and a space.')
        set_check(record, 'path_case', 'PASS', 'Application path contains non-ASCII text and whitespace.')
        current_check = 'clean_package_without_voice_models'
        if models_valid():
            raise ValueError('The starting package already contains valid voice models; use a clean source package.')
        set_check(record, 'clean_package_without_voice_models', 'PASS', 'Pinned voice assets were absent or incomplete before installation.')

        current_check = 'portable_install'
        installer = ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                     '-File', str(ROOT / 'install-portable.ps1'), '--force']
        if not command_ok(installer):
            raise RuntimeError('Portable installer failed.')
        set_check(record, 'portable_install', 'PASS', 'install-portable.ps1 --force exited with code 0.')
        python = ROOT / '.venv-portable/Scripts/python.exe'
        current_check = 'missing_voice_runtime'
        missing = [str(python), 'scripts/verify_runtime.py', '--missing-voice']
        if not command_ok(missing):
            raise RuntimeError('Missing-voice runtime verification failed.')
        set_check(record, 'missing_voice_runtime', 'PASS', 'verify_runtime.py --missing-voice exited with code 0.')
        for name in ('occupied_port_preserved', 'duplicate_start_preserved', 'owned_ports_released'):
            set_check(record, name, 'PASS', 'Covered by the successful isolated verify_runtime.py assertions.')

        if args.download_models:
            current_check = 'model_install_runtime'
            if not command_ok([str(python), 'voice/setup_local_voice_models.py', '--download']):
                raise RuntimeError('Pinned voice model installation failed.')
            if not models_valid() or not command_ok([str(python), 'scripts/verify_runtime.py']):
                raise RuntimeError('Runtime verification with installed voice models failed.')
            set_check(record, 'model_install_runtime', 'PASS', 'Pinned model hashes and runtime verification passed.')
        else:
            set_check(record, 'model_install_runtime', 'NOT_RUN', 'Run again with -DownloadModels to test pinned model installation.')
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        failed = True
        if record['checks'][current_check]['status'] == 'NOT_RUN':
            set_check(record, current_check, 'FAIL', f'Preflight stopped with {type(error).__name__}; see console output.')
        print(str(error), file=sys.stderr)
    path = write_record(record, output)
    status, errors = validate_record(record)
    if errors:
        print('INVALID: ' + '; '.join(errors), file=sys.stderr)
        return 1
    print(f'{status}: {path}')
    return 1 if failed or status == 'FAIL' else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='command', required=True)
    run = subparsers.add_parser('run')
    run.add_argument('--expected-commit', required=True)
    run.add_argument('--package-sha256', required=True)
    run.add_argument('--package-path', required=True, type=Path)
    run.add_argument('--powershell-version', required=True)
    run.add_argument('--chrome-version', required=True)
    run.add_argument('--download-models', action='store_true')
    validate = subparsers.add_parser('validate')
    validate.add_argument('record', type=Path)
    args = parser.parse_args()
    if args.command == 'run':
        return run_preflight(args)
    try:
        status, errors = validate_record(load_record(args.record))
    except (OSError, json.JSONDecodeError) as error:
        parser.exit(1, f'INVALID: {error}\n')
    if errors:
        parser.exit(1, 'INVALID: ' + '; '.join(errors) + '\n')
    print(status)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
