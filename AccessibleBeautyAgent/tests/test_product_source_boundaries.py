import json
from pathlib import Path

import pytest

from scripts.verify_product_source_boundaries import PRODUCTS, SOURCES, verify


def changed_copy(source, destination, mutate):
    payload = json.loads(Path(source).read_text(encoding='utf-8'))
    mutate(payload['records'])
    destination.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    return destination


def test_current_product_source_boundaries_pass():
    assert verify() == {'products': 14, 'source_backed': 2, 'demos': 12}


def test_unreviewed_claim_expansion_is_rejected(tmp_path):
    candidate = changed_copy(
        PRODUCTS,
        tmp_path / 'products.json',
        lambda rows: next(row for row in rows if row['product_id'] == 'maybelline_matte_ink').__setitem__(
            'claims', ['unreviewed wear claim']),
    )
    with pytest.raises(ValueError, match='outside the reviewed comparison scope'):
        verify(products_path=candidate)


def test_vinyl_normalization_explanation_is_required(tmp_path):
    candidate = changed_copy(
        SOURCES,
        tmp_path / 'sources.json',
        lambda rows: next(row for row in rows if row['source_id'] == 'maybelline_vinyl_ink_us_official').__setitem__(
            'notes', 'instant shine / vinyl finish'),
    )
    with pytest.raises(ValueError, match='normalized finish boundary'):
        verify(sources_path=candidate)
