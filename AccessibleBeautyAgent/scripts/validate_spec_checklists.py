"""Validate stage 1–8 review checklist structure and FR traceability."""
from pathlib import Path
import re
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


def expand_references(text):
    references = set()
    for match in FR_REFERENCE.finditer(text):
        first = int(match.group(1))
        last = int(match.group(2) or match.group(1))
        if last < first:
            raise ValueError(f'reversed FR range: {match.group(0)}')
        references.update(f'{value:03d}' for value in range(first, last + 1))
    return references


def validate_stage(directory):
    stage = STAGE_DIRECTORY.fullmatch(directory.name).group(1)
    spec = (directory / 'spec.md').read_text(encoding='utf-8')
    checklist = (directory / 'checklists/requirements.md').read_text(encoding='utf-8')
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
    for field in REVIEW_FIELDS:
        if checklist.count(f'- {field}') != 1:
            errors.append(f'review field must occur exactly once: {field}')
    return numbers, len(definitions), errors


def main():
    directories = sorted(
        path for path in SPECS_ROOT.iterdir()
        if path.is_dir() and STAGE_DIRECTORY.fullmatch(path.name)
    )
    if len(directories) != 8:
        print(f'INVALID: expected 8 stage directories, found {len(directories)}', file=sys.stderr)
        return 1
    all_numbers = []
    failures = []
    for directory in directories:
        numbers, fr_count, errors = validate_stage(directory)
        all_numbers.extend(numbers)
        if errors:
            failures.extend(f'{directory.name}: {error}' for error in errors)
        else:
            print(f'PASS {directory.name}: {len(numbers)} CHK, {fr_count} FR')
    duplicates = sorted({number for number in all_numbers if all_numbers.count(number) > 1})
    if duplicates:
        failures.append(f'global duplicate CHK numbers: {duplicates}')
    if failures:
        print('INVALID: ' + '; '.join(failures), file=sys.stderr)
        return 1
    print(f'PASS all stages: {len(all_numbers)} unique CHK with complete FR coverage and review metadata')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
