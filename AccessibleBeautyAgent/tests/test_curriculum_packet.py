from pathlib import Path

import pytest

from scripts.verify_curriculum_packet import verify


def test_curriculum_packet_matches_canonical_drafts():
    assert verify() == {'lessons': 10, 'review_fields': 80, 'visual_checks': 10, 'source_version': 2}


def test_curriculum_packet_verifier_rejects_changed_lesson_id(tmp_path):
    packet = Path(__file__).resolve().parents[2] / 'specs/003-dialogue-knowledge/curriculum-packet.md'
    changed = packet.read_text(encoding='utf-8').replace('`coaching_prep_zh` · v1', '`coaching_prep_changed_zh` · v1', 1)
    candidate = tmp_path / 'curriculum-packet.md'
    candidate.write_text(changed, encoding='utf-8')
    with pytest.raises(AssertionError, match='lesson IDs or order'):
        verify(candidate)
