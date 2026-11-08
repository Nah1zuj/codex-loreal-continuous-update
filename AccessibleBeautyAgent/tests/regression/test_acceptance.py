import base64
import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path):
    from app.main import create_app
    from app.config import Settings, ROOT
    with TestClient(create_app(Settings(model_provider='mock',vision_provider='mock',embedding_provider='mock',reranker_provider='mock',developer_mode=True,api_key='',memory_path=tmp_path / 'memory.sqlite',knowledge_dir=ROOT/'data/demo/knowledge'))) as c:
        yield c


def chat(client, text, sid=None, **extra):
    r = client.post('/api/chat', json={'message': text, 'session_id': sid, **extra})
    assert r.status_code == 200, r.text
    return r.json()


def test_health(client):
    h = client.get('/api/health').json()
    assert h['status'] == 'ok' and h['provider_mode'] == 'mock'
    assert all(h[x] for x in ('backend', 'agent', 'rag', 'vision', 'memory'))


def test_dinner_matches_soft_formal(client):
    r = chat(client, '今晚有一个正式 dinner，我想精致一点但别太成熟')
    assert r['session']['selected_look'] == 'soft_formal'
    assert r['session']['scene'] == 'dinner'
    assert 'too_mature' in r['session']['avoid']


def test_memory_requires_explicit_consent(client):
    r = client.post('/api/memory', json={'user_id': 'demo', 'candidate': {'feedback': 'lip too strong'}, 'explicit_consent': False})
    assert r.status_code == 403
    assert client.get('/api/profile/demo').json()['episodes'] == []


def test_memory_string_consent_rejected(client):
    r = client.post('/api/memory', json={'user_id': 'demo', 'candidate': {'feedback': 'test'}, 'explicit_consent': 'true'})
    assert r.status_code == 422


def test_memory_roundtrip_and_owner(client):
    draft=client.post('/api/memory/preview',json={'user_id':'demo','candidate':{
        'feedback':'唇色稍强','context':'dinner','preferred_saturation':'low'}}).json()
    r=client.post('/api/memory',json={'user_id':'demo',**draft,'explicit_consent':True})
    assert r.status_code == 200, r.text
    mid = r.json()['memory_id']
    assert client.get('/api/profile/demo').json()['profile']['preferred_saturation'] == 'low'
    assert client.delete(f'/api/memory/{mid}?user_id=other&explicit_consent=true').status_code == 404
    assert client.delete(f'/api/memory/{mid}?user_id=demo&explicit_consent=false').status_code == 403
    assert client.delete(f'/api/memory/{mid}?user_id=demo&explicit_consent=true').status_code == 200
    assert client.get('/api/profile/demo').json()['episodes'] == []


def test_rag_filter(client):
    r = client.post('/api/rag/search', json={'query': 'blush dinner', 'filters': {'scene': 'dinner'}, 'limit': 20}).json()
    assert r['results']
    assert all('dinner' in d['metadata']['scene'] for d in r['results'])


def test_unknown_session(client):
    assert client.get('/api/session/missing').status_code == 404


def test_no_fabricated_product_field(client):
    from app.products.service import describe_product
    p = describe_product({'product_id': 'unknown', 'brand': 'SAMPLE'})
    assert '不可用' in p
    assert '持久' not in p


def test_full_mock_journey(client):
    r = chat(client, '正式 dinner 不要成熟')
    sid = r['session']['session_id']
    r = chat(client, '开始步骤', sid)
    assert r['session']['stage'] == 'GUIDE'
    r = chat(client, 'next', sid)
    assert r['session']['routine_step'] == 1
    r = chat(client, 'check this', sid)
    assert r['session']['stage'] == 'CAMERA_CONSENT'
    assert not r['session']['camera_consent']
    r = chat(client, '', sid, action='camera_consent', consent=True)
    assert r['session']['camera_consent']
    v = client.post('/api/vision/check', json={'session_id': sid, 'task': 'blush_presence', 'demo': True, 'mock_status': 'BOTH', 'images': []})
    assert v.status_code == 200, v.text
    assert v.json()['visual']['status'] == 'BOTH'
    assert v.json()['visual']['simulated'] is True
    r = chat(client, '继续', sid)
    assert r['session']['routine_step'] == 2
    r = chat(client, 'next', sid)
    r = chat(client, 'skip', sid)
    assert r['session']['stage'] == 'FEEDBACK'
    r = chat(client, '唇色稍微太强，下次想淡一点', sid)
    assert r['session']['stage'] == 'MEMORY_CONSENT'
    assert client.get('/api/profile/demo').json()['episodes'] == []
    r = chat(client, '', sid, action='memory_consent', consent=True,
             memory_candidate_id=r['session']['memory_candidate_id'],
             memory_candidate_version=r['session']['memory_candidate_version'])
    assert r['session']['stage'] == 'COMPLETE'
    assert len(client.get('/api/profile/demo').json()['episodes']) == 1


def test_camera_revocation_blocks_upload(client):
    r = chat(client, 'dinner')
    sid = r['session']['session_id']
    chat(client, 'check this', sid)
    chat(client, '', sid, action='camera_consent', consent=True)
    r = chat(client, 'stop camera', sid)
    assert r['session']['camera_consent'] is False
    assert client.post('/api/vision/check', json={'session_id': sid, 'task': 'blush_presence', 'demo': True, 'images': []}).status_code == 403


def test_unknown_routine_and_advance_before_start(client):
    r = chat(client, 'dinner')
    sid = r['session']['session_id']
    assert client.post('/api/routine/start', json={'session_id': sid, 'routine_id': 'missing'}).status_code == 404
    assert client.post('/api/routine/advance', json={'session_id': sid}).status_code == 409


def test_low_confidence_has_no_correction(client):
    from app.vision.language import accessible_result
    from app.config import Settings
    text = accessible_result({'task': 'blush_presence', 'status': 'LEFT_ONLY', 'confidence': .3, 'simulated': False}, Settings())
    assert '不想随便猜' in text
    assert '补' not in text


def test_invalid_image(client):
    r = chat(client, 'dinner')
    sid = r['session']['session_id']
    chat(client, 'check this', sid)
    chat(client, '', sid, action='camera_consent', consent=True)
    r = client.post('/api/vision/gate', json={'session_id': sid, 'images': ['invalid']})
    assert r.status_code == 422
