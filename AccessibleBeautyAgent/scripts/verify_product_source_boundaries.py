"""Verify the repository boundary for the two source-backed comparison products."""
from collections import Counter
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = ROOT / 'data/knowledge/products.json'
SOURCES = ROOT / 'data/knowledge/sources.json'
REVIEW_DATE = '2026-11-12'
ALLOWED_PRODUCT_FIELDS = {
    'product_id', 'brand', 'name', 'category', 'finish', 'source', 'source_ids',
    'source_type', 'status', 'verified', 'demo_data',
}
ALLOWED_SOURCE_FIELDS = {
    'source_id', 'title', 'creator', 'url', 'accessed_at', 'source_type', 'notes',
}
EXPECTED = {
    'maybelline_matte_ink': {
        'name': 'Super Stay Matte Ink Liquid Lipstick',
        'finish': 'matte',
        'source_id': 'maybelline_matte_ink_us_official',
        'url': 'https://www.maybelline.com/lip-makeup/lipstick/superstay-matte-ink-liquid-lipstick',
        'title': 'Super Stay Matte Ink Liquid Lipstick · 官方资料（美国站）',
        'notes': '2026-11-12 复核美国官网：产品线名称、唇部类别和 matte 妆效仍受页面支持。应用未摘取价格、功效、具体色号、配方或持妆声明。',
    },
    'maybelline_vinyl_ink': {
        'name': 'Super Stay Vinyl Ink Longwear Liquid Lipcolor',
        'finish': 'glossy',
        'source_id': 'maybelline_vinyl_ink_us_official',
        'url': 'https://www.maybelline.com/lip-makeup/lipstick/super-stay-vinyl-ink-longwear-liquid-lipstick',
        'title': 'Super Stay Vinyl Ink Longwear Liquid Lipcolor · 官方资料（美国站）',
        'notes': '2026-11-12 复核美国官网：产品线名称、唇部类别和 instant shine / vinyl finish 仍受页面支持；应用中的 glossy 是亮泽类别归一化，不是官网逐字字段。应用未摘取价格、功效、具体色号、配方或持妆声明。',
    },
}
def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))['records']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def index_unique(records, key, label):
    require(isinstance(records, list) and all(isinstance(row, dict) for row in records),
            f'{label} records must be an array of objects.')
    identifiers = [row.get(key) for row in records]
    require(all(isinstance(value, str) and value for value in identifiers),
            f'{label} records must have nonempty {key} values.')
    duplicates = sorted(value for value, count in Counter(identifiers).items() if count > 1)
    require(not duplicates, f'{label} records contain duplicate {key} values: {duplicates}')
    return dict(zip(identifiers, records, strict=True))


def verify(products_path=PRODUCTS, sources_path=SOURCES):
    products = load(products_path)
    sources = load(sources_path)
    by_product = index_unique(products, 'product_id', 'Product')
    by_source = index_unique(sources, 'source_id', 'Source')
    require(all(type(row.get('demo_data')) is bool for row in products),
            'Every product demo_data value must be a boolean.')
    source_backed = [row for row in products if row['demo_data'] is False]
    demos = [row for row in products if row['demo_data'] is True]
    require(len(products) == 14 and len(demos) == 12 and len(source_backed) == 2,
            'Expected 14 products split into 12 demos and two source-backed drafts.')
    require(set(row['product_id'] for row in source_backed) == set(EXPECTED),
            'The source-backed product set changed and requires a new review.')

    for product_id, expected in EXPECTED.items():
        product = by_product[product_id]
        require(set(product) == ALLOWED_PRODUCT_FIELDS,
                f'{product_id} contains fields outside the reviewed comparison scope.')
        require(product['brand'] == 'Maybelline New York', f'{product_id} brand changed.')
        require(product['name'] == expected['name'], f'{product_id} name changed.')
        require(product['category'] == 'lip', f'{product_id} category changed.')
        require(product['finish'] == expected['finish'], f'{product_id} finish changed.')
        require(product['source'] == expected['source_id'], f'{product_id} primary source changed.')
        require(product['source_ids'] == [expected['source_id']], f'{product_id} source IDs changed.')
        require(product['source_type'] == 'official_brand', f'{product_id} source type changed.')
        require(product['status'] == 'DRAFT' and product['verified'] is False,
                f'{product_id} must remain an unreviewed draft until team review.')
        require(product['demo_data'] is False, f'{product_id} must remain source-backed, not demo data.')

        source = by_source[expected['source_id']]
        require(set(source) == ALLOWED_SOURCE_FIELDS,
                f'{product_id} source contains fields outside the reviewed scope.')
        require(source['title'] == expected['title'], f'{product_id} source title changed.')
        require(source['url'] == expected['url'], f'{product_id} official URL changed.')
        require(source['creator'] == 'Maybelline New York', f'{product_id} source creator changed.')
        require(source['source_type'] == 'official_brand', f'{product_id} source record type changed.')
        require(source['accessed_at'] == REVIEW_DATE, f'{product_id} source review date changed.')
        require(source['notes'] == expected['notes'],
                f'{product_id} source notes changed outside this review.')

    return {'products': len(products), 'source_backed': len(source_backed), 'demos': len(demos)}


if __name__ == '__main__':
    print('PASS product source boundaries:', verify())
