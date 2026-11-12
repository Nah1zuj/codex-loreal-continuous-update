import json
from pathlib import Path

from scripts.verify_target_user_trial_record import validate, verify


ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC = ROOT / 'specs/008-accessible-release/target-user-trial-record.synthetic.json'


def fixture():
    return json.loads(SYNTHETIC.read_text(encoding='utf-8'))


def real_record():
    record = fixture()
    record['evidence_class'] = 'real_target_user'
    record['participant_code'] = 'P-001'
    record['prerequisites'] = {
        'issue_8_professional_review': 'passed',
        'issue_11_engineering_candidate': 'passed',
    }
    record['environment'] = {
        'date': '2026-11-12',
        'platform': 'Windows x64',
        'browser': 'Chrome test version',
        'assistive_tool': 'NVDA',
        'assistive_tool_version': 'test version',
    }
    record['voluntary_conditions'] = {key: True for key in record['voluntary_conditions']}
    for task in record['tasks']:
        task['result'] = 'independent'
        task['observation'] = 'Synthetic unit-test observation.'
        task['understanding'] = 'Synthetic unit-test understanding.'
    record['qualification'] = {
        'critical_issues_open': 0,
        'decision': 'eligible',
        'rationale': 'Synthetic unit-test record satisfies explicit fields only.',
    }
    return record


def test_repository_synthetic_fixture_is_blocked():
    assert verify(SYNTHETIC) == ('BLOCKED', [])


def test_explicit_real_record_can_be_structurally_eligible():
    assert validate(real_record()) == ('ELIGIBLE', [])


def test_prompted_task_is_not_eligible_when_declared_consistently():
    record = real_record()
    record['tasks'][0]['result'] = 'prompted'
    record['tasks'][0]['help_count'] = 1
    record['qualification']['decision'] = 'not_eligible'
    assert validate(record) == ('NOT_ELIGIBLE', [])


def test_eligible_claim_cannot_bypass_blocked_prerequisite():
    record = real_record()
    record['prerequisites']['issue_11_engineering_candidate'] = 'blocked'
    status, errors = validate(record)
    assert status == 'INVALID'
    assert 'contradicts' in errors[0]


def test_real_record_requires_all_voluntary_conditions():
    record = real_record()
    record['voluntary_conditions']['stop_right_explained'] = False
    record['qualification']['decision'] = 'pending'
    status, errors = validate(record)
    assert status == 'INVALID'
    assert any('every voluntary condition' in error for error in errors)


def test_independent_result_cannot_include_operational_help():
    record = real_record()
    record['tasks'][1]['help_count'] = 1
    status, errors = validate(record)
    assert status == 'INVALID'
    assert any('cannot be independent with help' in error for error in errors)


def test_apparent_contact_information_is_rejected():
    record = real_record()
    record['tasks'][2]['observation'] = 'Contact me at person@example.com.'
    status, errors = validate(record)
    assert status == 'INVALID'
    assert any('email address' in error for error in errors)


def test_unknown_personal_field_is_rejected():
    record = real_record()
    record['participant_name'] = 'not allowed'
    status, errors = validate(record)
    assert status == 'INVALID'
    assert any('unexpected top-level fields' in error for error in errors)
