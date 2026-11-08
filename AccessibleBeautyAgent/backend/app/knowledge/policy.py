"""Shared admission checks for public knowledge, retrieval, and coaching."""


def is_retired(row):
    return row.get('status') in {'REJECTED', 'DEPRECATED'}


def is_reviewed(row):
    return (
        row.get('status') == 'HUMAN_VERIFIED' and row.get('verified') is True
        and bool((row.get('verified_by') or '').strip()) and bool(row.get('verified_at'))
        and not row.get('demo_data', False)
    )


def eligible(row, settings):
    if is_retired(row):
        return False
    return settings is None or settings.developer_mode or settings.research_mode or is_reviewed(row)
