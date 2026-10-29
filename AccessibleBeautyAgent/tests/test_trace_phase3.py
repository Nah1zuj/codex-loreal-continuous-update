import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.config import Settings,ROOT
from app.memory.store import MemoryStore


def test_memory_edit_requires_consent_and_owner(tmp_path):
    store=MemoryStore(tmp_path/'memory.sqlite')
    saved=store.save('owner',{'feedback':'old','preferred_saturation':'high'},True)
    mid=saved['memory_id']
    with pytest.raises(PermissionError):store.update('owner',mid,{'feedback':'new'},False)
    with pytest.raises(KeyError):store.update('other',mid,{'feedback':'new'},True)
    store.update('owner',mid,{'feedback':'new','preferred_saturation':'low'},True)
    profile=store.profile('owner')
    assert len(profile['episodes'])==1 and profile['episodes'][0]['memory_id']==mid
    assert profile['episodes'][0]['feedback']=='new' and profile['profile']['preferred_saturation']=='low'


def test_reading_mock_does_not_claim_real_observation():
    from app.reading.service import ReadingService
    service=ReadingService(Settings())
    result=service.read(b'image',demo=False)
    assert result['status']=='UNCERTAIN' and result['shade'] is None and result['simulated']
    demo=service.read(b'',demo=True)
    assert demo['simulated'] and demo['status']=='READ' and demo['shade']


def test_reading_remote_guard():
    from app.reading.service import ReadingService
    with pytest.raises(PermissionError):ReadingService(Settings(reading_provider='deepseek',allow_remote_ai=False)).read(b'image',demo=False)


def test_reading_api_refuses_missing_consent(tmp_path):
    from app.main import create_app
    app=create_app(Settings(memory_path=tmp_path/'test.sqlite'))
    with TestClient(app) as client:
        assert client.post('/api/reading/read',json={'demo':True,'explicit_consent':False}).status_code==403
        assert client.post('/api/reading/read',json={'demo':True,'explicit_consent':True}).json()['simulated']
        assert client.post('/api/reading/read',json={'demo':True,'explicit_consent':'true'}).status_code==422

def test_memory_edit_api_validation_and_owner(tmp_path):
    from app.main import create_app
    with TestClient(create_app(Settings(memory_path=tmp_path/'edit.sqlite'))) as client:
        payload={'user_id':'phase3-test','candidate':{'feedback':'test-only preference'},'explicit_consent':True}
        mid=client.post('/api/memory',json=payload).json()['memory_id']
        url='/api/memory/'+mid+'/edit'
        assert client.post(url,json={**payload,'explicit_consent':False}).status_code==403
        assert client.post(url,json={**payload,'user_id':'other'}).status_code==404
        assert client.post(url,json={**payload,'explicit_consent':'true'}).status_code==422
        assert client.post(url,json={**payload,'candidate':{'feedback':'updated test-only'}}).status_code==200
        episodes=client.get('/api/profile/phase3-test').json()['episodes']
        assert len(episodes)==1 and episodes[0]['feedback']=='updated test-only'


def test_reading_demo_disabled_in_production(tmp_path):
    from app.main import create_app
    with TestClient(create_app(Settings(memory_path=tmp_path/'read.sqlite',developer_mode=False))) as client:
        assert client.post('/api/reading/read',json={'demo':True,'explicit_consent':True}).status_code==403
