import json

import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings
from test_local_vision_permits import grant

def test_browser_owners_cannot_read_each_others_sessions_journals_or_memory(tmp_path):
    app=create_app(Settings(memory_path=tmp_path/'private.sqlite'))
    with TestClient(app) as a,TestClient(app) as b:
        session=a.post('/api/chat',json={'message':'日常'}).json()['session']
        assert b.get('/api/session/'+session['session_id']).status_code==404
        assert b.post('/api/chat',json={'session_id':session['session_id'],'message':'next'}).status_code==404
        a.post('/api/journal',json={'date':'2026-10-12','look':'A private entry','explicit_consent':True})
        assert len(a.get('/api/journal').json()['entries'])==1
        assert b.get('/api/journal').json()['entries']==[]
        assert b.get('/api/profile/'+session['user_id']).status_code==404

@pytest.mark.parametrize('headers', [
    pytest.param([], id='omitted'),
    pytest.param([('Content-Type','')], id='empty'),
    pytest.param([('Content-Type','Application/JSON; charset=utf-8')], id='case-insensitive'),
    pytest.param([('Content-Type','application/vnd.trace+json')], id='vendor-json'),
    pytest.param([('Content-Type','application/json'),('Content-Type','text/plain')], id='first-duplicate'),
])
def test_json_content_types_preserve_browser_ownership_for_sessions_and_journals(tmp_path, headers):
    app=create_app(Settings(memory_path=tmp_path/'json-ownership.sqlite'))
    with TestClient(app) as owner, TestClient(app) as other:
        session=owner.post('/api/experience/reflect',json={'locale':'en'}).json()['session']
        sid=session['session_id']
        advance=json.dumps({'session_id':sid,'message':'next','locale':'en'})
        assert other.post('/api/chat',content=advance,headers=headers).status_code==404
        assert owner.get('/api/session/'+sid).json()['makeup_plan']['active_index']==0
        advanced=owner.post('/api/chat',content=advance,headers=headers)
        assert advanced.status_code==200
        assert advanced.json()['session']['makeup_plan']['active_index']==1

        entry=json.dumps({'date':'2026-10-12','look':'A private entry','explicit_consent':True})
        saved=owner.post('/api/journal',content=entry,headers=headers)
        assert saved.status_code==200
        assert [entry['id'] for entry in owner.get('/api/journal').json()['entries']]==[saved.json()['id']]
        path='/api/journal/'+saved.json()['id']
        remove=json.dumps({'user_id':session['user_id'],'explicit_consent':True})
        assert other.request('DELETE',path,content=remove,headers=headers).status_code==404
        assert owner.request('DELETE',path,content=remove,headers=headers).status_code==200

def test_invalid_json_is_rejected_and_non_json_keeps_its_existing_validation(tmp_path):
    with TestClient(create_app(Settings(memory_path=tmp_path/'invalid-json.sqlite'))) as client:
        assert client.post('/api/chat',content=b'\xff').status_code==400
        assert client.post('/api/chat',content=b'{',headers={'Content-Type':'application/vnd.trace+json'}).status_code==400
        for headers in ([('Content-Type','text/plain')],
                        [('Content-Type','text/plain'),('Content-Type','application/json')]):
            assert client.post('/api/chat',content=b'{',headers=headers).status_code==422

def test_confirmed_transcript_has_retention_and_owner_deletion(tmp_path):
    app=create_app(Settings(memory_path=tmp_path/'retention.sqlite'))
    with TestClient(app) as c:
        sid=c.post('/api/chat/stream',json={'message':'今日虚构测试'}).text.split('"session_id": "')[1].split('"')[0]
        entry={'date':'2026-10-12','look':'Test','session_id':sid,'save_transcript':True,'explicit_consent':False}
        assert c.post('/api/journal',json=entry).status_code==403
        entry['explicit_consent']=True
        r=c.post('/api/journal',json=entry)
        assert r.status_code==200
        tid=r.json()['transcript_id']
        assert c.get('/api/transcript-records/'+tid).json()['messages'][0]['text']=='今日虚构测试'
        assert c.request('DELETE','/api/journal/'+r.json()['id'],json={'user_id':'demo','explicit_consent':True}).status_code==200
        assert c.get('/api/transcript-records/'+tid).status_code==404

def test_cross_origin_mutation_is_rejected(tmp_path):
    with TestClient(create_app(Settings(memory_path=tmp_path/'origin.sqlite'))) as c:
        assert c.post('/api/chat',json={'message':'x'},headers={'Origin':'https://untrusted.example'}).status_code==403

def test_production_admin_has_no_anonymous_bypass(tmp_path):
    with TestClient(create_app(Settings(memory_path=tmp_path/'admin.sqlite',developer_mode=False))) as c:
        assert c.get('/api/admin/dashboard').status_code==403

def test_local_frames_need_consent_freshness_and_unique_ids(tmp_path):
    import base64,cv2,numpy as np,time
    app=create_app(Settings(memory_path=tmp_path/'frames.sqlite'))
    app.state.agent.vision.gate.evaluate=lambda raw:{'gate_pass':True,'face_box':[30,20,100,120],'method':'synthetic_test_geometry'}
    with TestClient(app) as c:
        sid=c.post('/api/chat',json={'message':''}).json()['session']['session_id']
        raw=cv2.imencode('.png',np.full((160,160,3),120,np.uint8))[1].tobytes()
        frame={'session_id':sid,'image':base64.b64encode(raw).decode(),'frame_id':'new-1','captured_at':time.time(),'explicit_consent':False}
        assert c.post('/api/vision/local',json=frame).status_code==403
        frame['explicit_consent']=True
        assert c.post('/api/vision/local',json=frame).status_code==403
        frame['permit_id']=grant(c,sid)['permit_id']
        result=c.post('/api/vision/local',json=frame)
        assert result.status_code==200 and result.json()['observation']['confidence'] is None
        assert result.json()['frame_saved'] is False
        assert c.post('/api/vision/local',json=frame).status_code==409
        assert c.post('/api/vision/local',json={**frame,'frame_id':'new-2','captured_at':time.time()-60}).status_code==409

def test_demo_browser_origin_is_allowed_but_other_origins_are_still_rejected(tmp_path):
    settings=Settings(memory_path=tmp_path/'demo-origin.sqlite',model_provider='mock',allow_remote_ai=False,deepseek_api_key='',api_key='',compatible_api_key='')
    with TestClient(create_app(settings)) as c:
        from app.config import DEFAULT_FRONTEND
        for origin in [f'http://127.0.0.1:{DEFAULT_FRONTEND}',f'http://localhost:{DEFAULT_FRONTEND}']:
            response=c.post('/api/session',json={'locale':'zh-CN'},headers={'Origin':origin})
            assert response.status_code==200
        for origin in ['https://untrusted.example','http://127.0.0.1:5181']:
            assert c.post('/api/session',json={},headers={'Origin':origin}).status_code==403
