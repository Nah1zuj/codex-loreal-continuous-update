from fastapi.testclient import TestClient

from app.config import ROOT, Settings
from app.main import create_app


def test_complete_look_reply_is_warm_independent_and_brand_neutral(tmp_path):
    settings = Settings(
        memory_path=tmp_path / 'independent.sqlite',
        knowledge_dir=ROOT / 'data/demo/knowledge',
    )
    with TestClient(create_app(settings)) as client:
        reply = client.post(
            '/api/chat', json={'message': '想要一套完整造型建议'}
        ).json()['message']
    assert '不限定任何品牌' in reply
    assert '已有的物品' in reply or '熟悉' in reply
    for restricted in ('欧莱雅', '支付宝', '比赛', 'L’Oréal', 'Maybelline'):
        assert restricted not in reply


def test_product_catalog_uses_item_names_and_broad_categories(tmp_path):
    settings = Settings(
        memory_path=tmp_path / 'catalog.sqlite',
        knowledge_dir=ROOT / 'data/demo/knowledge',
    )
    with TestClient(create_app(settings)) as client:
        rows = client.get('/api/products/catalog').json()['results']
    assert rows and all(set(row) == {'product_id', 'name', 'category'} for row in rows)
    assert {row['category'] for row in rows} == {
        'skincare', 'base', 'eye', 'brow', 'blush', 'lip', 'hair', 'fragrance', 'accessories'
    }
