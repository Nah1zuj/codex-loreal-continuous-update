"""Validate stage 1–8 review checklist structure and FR traceability."""
import argparse
from pathlib import Path
import re
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
SPECS_ROOT = REPO_ROOT / 'specs'
STAGE_DIRECTORY = re.compile(r'^00([1-8])-.+$')
FR_DEFINITION = re.compile(
    r'(?m)^(?:-\s+(?:\*\*)?FR-(\d{3})|\|[^|]*\|\s*FR-(\d{3})\b)'
)
CHECK_LINE = re.compile(r'(?m)^- \[[ x]\] CHK(\d{3})\s+.*?\[([^\]]+)\]\s*$')
FR_REFERENCE = re.compile(r'FR-(\d{3})(?:[–-]FR-(\d{3}))?')
REVIEW_FIELDS = (
    '评审者：', '评审日期：', '审查 Git 版本：',
    '已查看范围：', '结论：', '保留项：',
)
REVIEW_PLACEHOLDERS = {'', '待填写'}


def git_output(*args):
    result = subprocess.run(
        ['git', '-C', str(REPO_ROOT), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise ValueError(detail or f'git command failed: {args}')
    return result.stdout


def git_snapshot(commit):
    resolved = git_output('rev-parse', '--verify', f'{commit}^{{commit}}').strip()
    names = git_output('ls-tree', '-d', '--name-only', f'{resolved}:specs').splitlines()

    def read_text(relative_path):
        return git_output('show', f'{resolved}:{relative_path.as_posix()}')

    return resolved, names, read_text


def expand_references(text):
    references = set()
    for match in FR_REFERENCE.finditer(text):
        first = int(match.group(1))
        last = int(match.group(2) or match.group(1))
        if last < first:
            raise ValueError(f'reversed FR range: {match.group(0)}')
        references.update(f'{value:03d}' for value in range(first, last + 1))
    return references


def validate_stage(directory_name, read_text):
    stage = STAGE_DIRECTORY.fullmatch(directory_name).group(1)
    base = Path('specs') / directory_name
    spec = read_text(base / 'spec.md')
    checklist = read_text(base / 'checklists/requirements.md')
    definitions = {next(value for value in match.groups() if value) for match in FR_DEFINITION.finditer(spec)}
    checks = CHECK_LINE.findall(checklist)
    errors = []
    if not definitions:
        errors.append('no FR definitions found')
    if not checks:
        errors.append('no CHK entries found')
    numbers = [number for number, _ in checks]
    expected_prefix = '0' if stage == '1' else stage
    if any(not number.startswith(expected_prefix) for number in numbers):
        errors.append(f'CHK number outside stage {stage}: {numbers}')
    if len(numbers) != len(set(numbers)):
        errors.append('duplicate CHK number within stage')
    numeric = [int(number) for number in numbers]
    if numeric and numeric != list(range(numeric[0], numeric[0] + len(numeric))):
        errors.append(f'CHK numbers are not continuous: {numbers}')
    references = set()
    for number, reference_text in checks:
        try:
            expanded = expand_references(reference_text)
        except ValueError as error:
            errors.append(f'CHK{number} {error}')
            continue
        if not expanded:
            errors.append(f'CHK{number} has no FR reference')
        references.update(expanded)
    invalid = sorted(references - definitions)
    missing = sorted(definitions - references)
    if invalid:
        errors.append(f'undefined FR references: {invalid}')
    if missing:
        errors.append(f'FR definitions without CHK coverage: {missing}')
    if checklist.count('## 评审记录（由实际评审者填写）') != 1:
        errors.append('review record section must occur exactly once')
    review_values = []
    for field in REVIEW_FIELDS:
        if checklist.count(f'- {field}') != 1:
            errors.append(f'review field must occur exactly once: {field}')
            continue
        value = checklist.split(f'- {field}', 1)[1].splitlines()[0].strip()
        review_values.append(value)
    normalized = [value if value not in REVIEW_PLACEHOLDERS else '' for value in review_values]
    if any(normalized) and not all(normalized):
        errors.append('review record is partially filled')
    review_status = 'completed' if normalized and all(normalized) else 'pending'
    return numbers, len(definitions), review_status, errors


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--commit',
        help='read specs from an immutable Git commit instead of the working tree',
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        if args.commit:
            source, names, read_text = git_snapshot(args.commit)
            source_label = f'commit {source}'
        else:
            names = [path.name for path in SPECS_ROOT.iterdir() if path.is_dir()]
            read_text = lambda relative: (REPO_ROOT / relative).read_text(encoding='utf-8')
            source_label = 'working tree (may include uncommitted changes)'
    except (OSError, ValueError) as error:
        print(f'INVALID: cannot read validation source: {error}', file=sys.stderr)
        return 1
    directories = sorted(name for name in names if STAGE_DIRECTORY.fullmatch(name))
    if len(directories) != 8:
        print(f'INVALID: expected 8 stage directories, found {len(directories)}', file=sys.stderr)
        return 1
    all_numbers = []
    review_statuses = []
    failures = []
    for directory in directories:
        try:
            numbers, fr_count, review_status, errors = validate_stage(directory, read_text)
        except (OSError, ValueError) as error:
            failures.append(f'{directory}: cannot read stage files: {error}')
            continue
        all_numbers.extend(numbers)
        review_statuses.append(review_status)
        if errors:
            failures.extend(f'{directory}: {error}' for error in errors)
        else:
            print(f'PASS {directory}: {len(numbers)} CHK, {fr_count} FR, review {review_status}')
    duplicates = sorted({number for number in all_numbers if all_numbers.count(number) > 1})
    if duplicates:
        failures.append(f'global duplicate CHK numbers: {duplicates}')
    if failures:
        print('INVALID: ' + '; '.join(failures), file=sys.stderr)
        return 1
    completed = review_statuses.count('completed')
    pending = review_statuses.count('pending')
    print(f'PASS source: {source_label}')
    print(f'PASS all stages: {len(all_numbers)} unique CHK with complete FR coverage')
    print(f'REVIEW RECORDS: {completed} completed, {pending} pending')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
