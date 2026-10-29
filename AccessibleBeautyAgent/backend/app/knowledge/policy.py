def eligible(row,settings):
    if row.get('status') in ('REJECTED','DEPRECATED'):return False
    return settings is None or settings.developer_mode or settings.research_mode or (row.get('verified') is True and not row.get('demo_data',False))
