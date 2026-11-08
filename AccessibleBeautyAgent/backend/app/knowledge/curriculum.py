"""Select complete, rights-cleared courses from the canonical knowledge store."""

from app.knowledge.policy import is_reviewed, is_retired
from app.schemas.makeup import Lesson, LessonProvenance, MakeupStep, PlanProposal

TEMPLATES = {
    'natural': ('自然日常', 'Natural everyday', ('prep', 'foundation', 'blush', 'lips', 'finish')),
    'warm': ('柔和暖调', 'Soft warm', ('prep', 'foundation', 'eyes', 'blush', 'lips', 'finish')),
    'professional': ('简约通勤', 'Minimal professional', ('prep', 'foundation', 'concealer', 'brows', 'lips', 'finish')),
    'evening': ('柔和晚间', 'Gentle evening', ('prep', 'foundation', 'eyes', 'blush', 'lips', 'finish')),
    'beginner': ('简单初学', 'Simple beginner', ('prep', 'blush', 'lips', 'finish')),
}
STANDARD = ('prep', 'primer', 'foundation', 'concealer', 'brows', 'eyes', 'blush', 'lips', 'finish')
PRODUCT_TOPICS = {
    'primer': ('妆前乳', 'primer'),
    'foundation': ('底妆', '粉底', '气垫', 'foundation', 'base makeup'),
    'concealer': ('遮瑕', 'concealer'),
    'brows': ('眉笔', '画眉', '眉妆', 'brow'),
    'eyes': ('眼妆', '眼影', '眼线', 'eye makeup', 'eyeshadow', 'eyeliner', 'mascara'),
    'blush': ('腮红', 'blush', 'rouge'),
    'lips': ('口红', '唇妆', '唇膏', 'lipstick', 'lip makeup', 'lip color'),
}


def source_permission(row):
    return (
        not is_retired(row) and not row.get('demo_data')
        and row.get('use_permission') in {'original', 'cc-by', 'cc0', 'licensed'}
        and bool((row.get('use_basis') or '').strip())
        and bool(row.get('url') or row.get('local_file'))
    )


def lesson_sources(row, source_map):
    sources = [source_map.get(source_id) for source_id in row.get('source_ids', [])]
    if not sources or any(source is None or not source_permission(source) for source in sources):
        return []
    return sources


def lesson_rows(store, locale, *, reviewed_only):
    source_map = {source['source_id']: source for source in store.sources}
    return [
        row for row in store.guidance
        if row.get('category') == 'makeup_lesson' and locale in row.get('tags', [])
        and row.get('teaching') and not is_retired(row)
        and not row.get('demo_data') and lesson_sources(row, source_map)
        and (not reviewed_only or is_reviewed(row))
    ]


def course_topics(needs):
    topics = STANDARD if needs.complexity == 'standard' and needs.minutes >= 30 else TEMPLATES[needs.style][2]
    # Recognized exclusions omit the matching makeup operation, leaving preparation and finish.
    avoid = ' '.join(needs.avoid).casefold()
    return [topic for topic in topics if not any(term in avoid for term in PRODUCT_TOPICS.get(topic, ()))]


def course_options(rows, needs):
    return [
        [row for row in rows if topic in row['tags'] and (not row.get('scene') or needs.occasion in row['scene'])]
        for topic in course_topics(needs)
    ]


def select_course(rows, needs, candidate):
    choices = course_options(rows, needs)
    if not all(choices):
        return [], False
    if candidate is not None:
        try:
            ids = PlanProposal.model_validate(candidate).lesson_ids
            if len(ids) != len(choices) or len(set(ids)) != len(ids):
                raise ValueError('Incomplete or repeated course steps')
            selected = [
                next(row for row in options if row['guidance_id'] == lesson_id)
                for options, lesson_id in zip(choices, ids)
            ]
            return selected, False
        except (StopIteration, ValueError):
            return [options[0] for options in choices], True
    return [options[0] for options in choices], False


def make_steps(selected, sources):
    source_map = {source['source_id']: source for source in sources}
    return [
        MakeupStep(
            id=row['guidance_id'], order=order, title=row['principle'],
            source_id=row['guidance_id'], review_status=row['status'],
            lesson_provenance=LessonProvenance(
                version=row['version'], reviewed_by=row.get('verified_by'), reviewed_at=row.get('verified_at'),
                sources=[
                    {key: source[key] for key in (
                        'source_id', 'title', 'version', 'url', 'local_file', 'use_permission', 'use_basis',
                    )}
                    for source in lesson_sources(row, source_map)
                ],
            ),
            **Lesson.model_validate(row['teaching']).model_dump(),
        )
        for order, row in enumerate(selected, 1)
    ]
