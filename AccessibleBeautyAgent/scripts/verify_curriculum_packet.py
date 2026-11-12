"""Verify that the professional-review packet mirrors the canonical draft lessons."""
from collections import Counter
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
TOPICS = ('prep', 'foundation', 'blush', 'lips', 'finish')
LANGUAGES = ('zh', 'en')
TEACHING_FIELDS = (
    'purpose', 'requiredProducts', 'preparation', 'instructions',
    'accessibilityInstructions', 'commonMistakes', 'completionCriteria',
)
FIELD_LABELS = {
    'zh': ('目的', '所需用具与产品', '操作前准备', '操作步骤', '辅助定位与操作', '常见失误', '本人确认标准'),
    'en': ('Purpose', 'Tools and products', 'Preparation', 'Instructions', 'Accessible guidance', 'Common mistakes', 'Self-confirmation criteria'),
}
PINNED_COMMIT = 'db485ed098d433758358e8cc6280af5d4003afe1'


def load_records(path):
    return json.loads(path.read_text(encoding='utf-8'))['records']


def load_pinned_records(path):
    relative = path.relative_to(REPO).as_posix()
    payload = subprocess.check_output(
        ['git', '-C', str(REPO), 'show', f'{PINNED_COMMIT}:{relative}'],
        text=True,
    )
    return json.loads(payload)['records']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(packet_path=None, guidance_path=None, sources_path=None):
    packet_path = packet_path or REPO / 'specs/003-dialogue-knowledge/curriculum-packet.md'
    guidance_path = guidance_path or ROOT / 'data/knowledge/accessibility_guidance.json'
    sources_path = sources_path or ROOT / 'data/knowledge/sources.json'
    packet = packet_path.read_text(encoding='utf-8')
    guidance = load_records(guidance_path)
    sources = load_records(sources_path)
    pinned_guidance = load_pinned_records(ROOT / 'data/knowledge/accessibility_guidance.json')
    pinned_sources = load_pinned_records(ROOT / 'data/knowledge/sources.json')
    expected_ids = [f'coaching_{topic}_{language}' for topic in TOPICS for language in LANGUAGES]
    by_id = {row['guidance_id']: row for row in guidance}
    pinned_by_id = {row['guidance_id']: row for row in pinned_guidance}
    require(all(guidance_id in by_id for guidance_id in expected_ids), 'A required bilingual lesson is missing.')
    require(
        all(by_id[guidance_id] == pinned_by_id.get(guidance_id) for guidance_id in expected_ids),
        'A current lesson differs from the pinned Git snapshot; update the commit and repeat review.',
    )
    lessons = [by_id[guidance_id] for guidance_id in expected_ids]

    packet_ids = re.findall(r'`(coaching_(?:prep|foundation|blush|lips|finish)_(?:zh|en))` · v1', packet)
    require(packet_ids == expected_ids, 'The packet lesson IDs or order differ from the canonical five bilingual pairs.')
    require(PINNED_COMMIT in packet, 'The review packet does not identify its pinned Git commit.')

    review_fragments = []
    for row in lessons:
        require(row['status'] == 'DRAFT' and row['verified'] is False, 'A lesson is no longer an unreviewed draft.')
        require(row['source'] == 'trace_original_phase4', 'A lesson uses an unexpected primary source.')
        require(row['source_ids'] == ['trace_original_phase4'], 'A lesson uses unexpected source IDs.')
        language = row['guidance_id'].rsplit('_', 1)[1]
        heading = '简体中文' if language == 'zh' else 'English'
        review_fragments.append(f'### {heading} · {row["principle"]}')
        teaching = row['teaching']
        for field, label in zip(TEACHING_FIELDS, FIELD_LABELS[language], strict=True):
            field_values = teaching[field]
            if isinstance(field_values, list):
                require(len(field_values) == 1, f'{row["guidance_id"]}.{field} is not a single review field.')
                value = field_values[0]
            else:
                value = field_values
            review_fragments.append(f'- **{label}** {value}')
    require(len(review_fragments) == 80, 'Expected ten lessons with eight review fields each.')
    for fragment, count in Counter(review_fragments).items():
        require(packet.count(fragment) == count, f'The packet differs for canonical field: {fragment!r}')

    optional = [row['teaching']['optionalVisualCheck'] for row in lessons]
    require(optional.count(None) == 6, 'The pinned lessons have an unexpected number of empty visual checks.')
    require(packet.count('**可选视觉检查** 未设置') == 3, 'Chinese empty visual checks differ from the records.')
    require(packet.count('**Optional visual check** Not set') == 3, 'English empty visual checks differ from the records.')
    require(packet.count('`blush_presence`') == 2, 'Blush visual checks differ from the records.')
    require(packet.count('`lip_presence`') == 2, 'Lip visual checks differ from the records.')

    source = next(row for row in sources if row['source_id'] == 'trace_original_phase4')
    pinned_source = next(row for row in pinned_sources if row['source_id'] == 'trace_original_phase4')
    require(source == pinned_source, 'The current source record differs from the pinned Git snapshot.')
    require(source['version'] == 2 and source['status'] == 'DRAFT' and source['verified'] is False,
            'The pinned source record is not the expected unreviewed v2 draft.')
    require(source['use_permission'] == 'original' and source['use_basis'].strip(),
            'The source permission or use basis is missing.')
    require('trace_original_phase4` v2' in packet, 'The packet does not identify source v2.')
    require(source['use_basis'] in packet, 'The packet omits the source use basis.')
    return {'lessons': len(lessons), 'review_fields': len(review_fragments), 'visual_checks': len(optional), 'source_version': source['version']}


if __name__ == '__main__':
    result = verify()
    print('PASS curriculum packet matches pinned draft records:', result)
