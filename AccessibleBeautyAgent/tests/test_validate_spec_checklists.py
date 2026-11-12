import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / 'scripts' / 'validate_spec_checklists.py'
SPEC = importlib.util.spec_from_file_location('validate_spec_checklists', SCRIPT)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def stage_reader(review_values=None):
    values = {
        '评审者：': '',
        '评审日期：': '',
        '审查 Git 版本：': '',
        '已查看范围：': '',
        '结论：': '待填写',
        '保留项：': '',
    }
    values.update(review_values or {})
    checklist = '\n'.join([
        '## 评审记录（由实际评审者填写）',
        *(f'- {field}{value}' for field, value in values.items()),
        '',
        '- [ ] CHK001 核对要求 [FR-101]',
    ])

    def read_text(path):
        if path.name == 'spec.md':
            return '- **FR-101** 示例要求。\n'
        return checklist

    return read_text


def test_pending_review_is_reported_without_becoming_a_signature():
    numbers, fr_count, status, errors = validator.validate_stage(
        '001-runtime-baseline', stage_reader()
    )
    assert numbers == ['001']
    assert fr_count == 1
    assert status == 'pending'
    assert errors == []


def test_partially_filled_review_is_rejected():
    _, _, status, errors = validator.validate_stage(
        '001-runtime-baseline', stage_reader({'评审者：': '示例评审者'})
    )
    assert status == 'pending'
    assert 'review record is partially filled' in errors


def test_complete_review_requires_all_six_values():
    values = {
        '评审者：': '示例评审者',
        '评审日期：': '2026-11-12',
        '审查 Git 版本：': '0123456',
        '已查看范围：': '阶段 1',
        '结论：': '保留意见',
        '保留项：': 'Windows 实机待验',
    }
    _, _, status, errors = validator.validate_stage(
        '001-runtime-baseline', stage_reader(values)
    )
    assert status == 'completed'
    assert errors == []


def test_reversed_fr_range_is_rejected_without_assertions():
    with pytest.raises(ValueError, match='reversed FR range'):
        validator.expand_references('FR-106–FR-101')
