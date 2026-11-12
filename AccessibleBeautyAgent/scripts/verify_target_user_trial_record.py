"""Validate an anonymized target-user trial record without asserting that it is genuine."""
import argparse
from datetime import date
import json
from pathlib import Path
import re


TASK_IDS = {
    'start_pause_resume',
    'deny_media_continue_text',
    'summary_save_or_discard',
}
RESULTS = {'independent', 'prompted', 'not_completed', 'withdrawn'}
PREREQUISITE_STATES = {'passed', 'blocked'}
DECISIONS = {'eligible', 'not_eligible', 'pending'}
TOP_LEVEL_KEYS = {
    'schema_version', 'record_kind', 'evidence_class', 'participant_code',
    'trial_commit', 'package_sha256', 'prerequisites', 'environment',
    'voluntary_conditions', 'tasks', 'qualification',
}
TASK_KEYS = {'task_id', 'result', 'help_count', 'observation', 'understanding', 'issue_refs'}
EMAIL = re.compile(r'(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b')
CN_MOBILE = re.compile(r'(?<!\d)1[3-9]\d{9}(?!\d)')


def nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def validate(record):
    errors = []
    if not isinstance(record, dict):
        return 'INVALID', ['record must be a JSON object']
    missing = TOP_LEVEL_KEYS - record.keys()
    extra = record.keys() - TOP_LEVEL_KEYS
    if missing:
        errors.append(f'missing top-level fields: {sorted(missing)}')
    if extra:
        errors.append(f'unexpected top-level fields: {sorted(extra)}')
    if errors:
        return 'INVALID', errors

    if record['schema_version'] != 1:
        errors.append('schema_version must be 1')
    if record['record_kind'] != 'target_user_trial_observation':
        errors.append('record_kind is invalid')
    evidence = record['evidence_class']
    if evidence not in {'real_target_user', 'synthetic_fixture'}:
        errors.append('evidence_class is invalid')
    code = record['participant_code']
    expected_code = r'P-\d{3,}' if evidence == 'real_target_user' else r'SYNTHETIC-\d{3,}'
    if not isinstance(code, str) or not re.fullmatch(expected_code, code):
        errors.append('participant_code does not match the evidence class')
    if not isinstance(record['trial_commit'], str) or not re.fullmatch(r'[0-9a-f]{40}', record['trial_commit']):
        errors.append('trial_commit must be a full lowercase Git SHA')
    if not isinstance(record['package_sha256'], str) or not re.fullmatch(r'[0-9a-f]{64}', record['package_sha256']):
        errors.append('package_sha256 must be a lowercase SHA-256')

    prerequisites = record['prerequisites']
    expected_prerequisites = {'issue_8_professional_review', 'issue_11_engineering_candidate'}
    if not isinstance(prerequisites, dict) or set(prerequisites) != expected_prerequisites:
        errors.append('prerequisites must contain exactly Issue #8 and Issue #11 states')
        prerequisites = {}
    elif any(value not in PREREQUISITE_STATES for value in prerequisites.values()):
        errors.append('prerequisite states must be passed or blocked')

    environment = record['environment']
    environment_keys = {'date', 'platform', 'browser', 'assistive_tool', 'assistive_tool_version'}
    if not isinstance(environment, dict) or set(environment) != environment_keys:
        errors.append('environment fields are incomplete or unexpected')
    else:
        if not all(nonempty_string(environment[key]) for key in environment_keys):
            errors.append('environment fields must be non-empty strings')
        try:
            date.fromisoformat(environment['date'])
        except (TypeError, ValueError):
            errors.append('environment.date must use YYYY-MM-DD')

    voluntary = record['voluntary_conditions']
    voluntary_keys = {'information_provided', 'voluntary_agreement', 'stop_right_explained', 'data_boundary_explained'}
    if not isinstance(voluntary, dict) or set(voluntary) != voluntary_keys:
        errors.append('voluntary_conditions fields are incomplete or unexpected')
        voluntary = {}
    elif any(type(value) is not bool for value in voluntary.values()):
        errors.append('voluntary_conditions values must be booleans')

    tasks = record['tasks']
    seen = set()
    if not isinstance(tasks, list) or len(tasks) != len(TASK_IDS):
        errors.append('tasks must contain exactly three observations')
        tasks = []
    for index, task in enumerate(tasks):
        if not isinstance(task, dict) or set(task) != TASK_KEYS:
            errors.append(f'task {index} fields are incomplete or unexpected')
            continue
        task_id = task['task_id']
        if task_id not in TASK_IDS or task_id in seen:
            errors.append(f'task {index} has an invalid or duplicate task_id')
        seen.add(task_id)
        if task['result'] not in RESULTS:
            errors.append(f'task {task_id} has an invalid result')
        if type(task['help_count']) is not int or task['help_count'] < 0:
            errors.append(f'task {task_id} help_count must be a non-negative integer')
        if task['result'] == 'independent' and task['help_count'] != 0:
            errors.append(f'task {task_id} cannot be independent with help')
        if task['result'] == 'prompted' and task['help_count'] < 1:
            errors.append(f'task {task_id} prompted result requires help_count')
        if not nonempty_string(task['observation']) or not nonempty_string(task['understanding']):
            errors.append(f'task {task_id} observation and understanding must be non-empty')
        refs = task['issue_refs']
        if not isinstance(refs, list) or any(type(ref) is not int or ref < 1 for ref in refs):
            errors.append(f'task {task_id} issue_refs must contain positive issue numbers')
    if seen != TASK_IDS:
        errors.append('the three required task IDs are not all present')

    qualification = record['qualification']
    qualification_keys = {'critical_issues_open', 'decision', 'rationale'}
    if not isinstance(qualification, dict) or set(qualification) != qualification_keys:
        errors.append('qualification fields are incomplete or unexpected')
        qualification = {}
    else:
        if type(qualification['critical_issues_open']) is not int or qualification['critical_issues_open'] < 0:
            errors.append('critical_issues_open must be a non-negative integer')
        if qualification['decision'] not in DECISIONS:
            errors.append('qualification.decision is invalid')
        if not nonempty_string(qualification['rationale']):
            errors.append('qualification.rationale must be non-empty')

    for value in strings(record):
        if EMAIL.search(value) or CN_MOBILE.search(value):
            errors.append('record contains an apparent email address or mainland China mobile number')
            break
    if errors:
        return 'INVALID', errors

    prerequisites_passed = all(value == 'passed' for value in prerequisites.values())
    conditions_passed = all(voluntary.values())
    if evidence == 'real_target_user' and not conditions_passed:
        return 'INVALID', ['real target-user evidence requires every voluntary condition to be true']
    all_independent = all(task['result'] == 'independent' for task in tasks)
    no_critical_issues = qualification['critical_issues_open'] == 0
    derived_eligible = (
        evidence == 'real_target_user' and prerequisites_passed and conditions_passed
        and all_independent and no_critical_issues
    )
    declared = qualification['decision']
    if declared == 'eligible' and not derived_eligible:
        return 'INVALID', ['eligible decision contradicts the explicit gates or observations']
    if derived_eligible and declared != 'eligible':
        return 'INVALID', ['all explicit eligibility gates pass but decision is not eligible']
    if evidence != 'real_target_user' or not prerequisites_passed or declared == 'pending':
        return 'BLOCKED', []
    return ('ELIGIBLE' if derived_eligible else 'NOT_ELIGIBLE'), []


def verify(path):
    record = json.loads(Path(path).read_text(encoding='utf-8'))
    return validate(record)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record', type=Path)
    args = parser.parse_args()
    try:
        status, errors = verify(args.record)
    except (OSError, json.JSONDecodeError) as error:
        parser.exit(1, f'INVALID: {error}\n')
    if errors:
        parser.exit(1, 'INVALID: ' + '; '.join(errors) + '\n')
    print(status)
