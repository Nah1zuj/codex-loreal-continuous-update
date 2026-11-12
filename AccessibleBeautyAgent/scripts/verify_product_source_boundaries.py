"""Verify the repository boundary for the two source-backed comparison products."""
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
EXPECTED = {
    'maybelline_matte_ink': {
        'name': 'Super Stay Matte Ink Liquid Lipstick',
        'finish': 'matte',
        'source_id': 'maybelline_matte_ink_us_official',
        'url': 'https://www.maybelline.com/lip-makeup/lipstick/superstay-matte-ink-liquid-lipstick',
        'source_terms': ('matte',),
    },
    'maybelline_vinyl_ink': {
        'name': 'Super Stay Vinyl Ink Longwear Liquid Lipcolor',
        'finish': 'glossy',
        'source_id': 'maybelline_vinyl_ink_us_official',
        'url': 'https://www.maybelline.com/lip-makeup/lipstick/super-stay-vinyl-ink-longwear-liquid-lipstick',
        'source_terms': ('instant shine', 'vinyl finish', 'glossy', '归一化', '不是官网逐字字段'),
    },
}
EXCLUDED_SCOPE_TERMS = ('价格', '功效', '具体色号', '配方', '持妆声明')


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))['records']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(products_path=PRODUCTS, sources_path=SOURCES):
    products = load(products_path)
    sources = load(sources_path)
    by_product = {row['product_id']: row for row in products}
    by_source = {row['source_id']: row for row in sources}
    source_backed = [row for row in products if not row.get('demo_data', False)]
    demos = [row for row in products if row.get('demo_data', False)]
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

        source = by_source[expected['source_id']]
        require(source['url'] == expected['url'], f'{product_id} official URL changed.')
        require(source['creator'] == 'Maybelline New York', f'{product_id} source creator changed.')
        require(source['source_type'] == 'official_brand', f'{product_id} source record type changed.')
        require(source['accessed_at'] == REVIEW_DATE, f'{product_id} source review date changed.')
        notes = source.get('notes', '')
        require(all(term in notes for term in expected['source_terms']),
                f'{product_id} source notes omit a required direct or normalized finish boundary.')
        require(all(term in notes for term in EXCLUDED_SCOPE_TERMS),
                f'{product_id} source notes omit an excluded field boundary.')

    return {'products': len(products), 'source_backed': len(source_backed), 'demos': len(demos)}


if __name__ == '__main__':
    print('PASS product source boundaries:', verify())
