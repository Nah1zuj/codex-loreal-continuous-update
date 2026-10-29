from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings

def configured(path):return Settings(memory_path=path,model_provider='mock',vision_provider='mock',embedding_provider='mock',reading_provider='mock',reference_provider='mock',allow_remote_ai=False)

def begin(client):
    reply=client.post('/api/experience/reflect',json={})
    assert reply.status_code==200,reply.text
    return reply.json()['session']['session_id']

def test_next_visit_summary_is_durable_and_no_authorization_flow(tmp_path):
    path=tmp_path/'recollection.sqlite'
    with TestClient(create_app(configured(path))) as client:
        sid=begin(client)
        reply=client.post('/api/recollection/finish',json={'session_id':sid})
        assert reply.status_code==200
        summary=client.get('/api/recollection').json()
        assert summary['latest']['session_id']==sid
        assert summary['latest']['completed_steps']==[]
        assert not summary['latest']['all_steps_completed']
        assert '授权' not in reply.json()['message']
        client.post('/api/recollection/finish',json={'session_id':sid})
        assert len(client.get('/api/recollection').json()['entries'])==1
        cookies=dict(client.cookies)
    with TestClient(create_app(configured(path))) as returning:
        returning.cookies.update(cookies)
        assert returning.get('/api/recollection').json()['latest']['session_id']==sid
        with returning.app.state.agent.memory.connect() as db:
            assert db.execute('SELECT COUNT(*) FROM memories').fetchone()[0]==0

def test_owners_settings_and_clear_do_not_leak_or_block_new_flow(tmp_path):
    app=create_app(configured(tmp_path/'owners.sqlite'))
    with TestClient(app) as a,TestClient(app) as b:
        sid=begin(a)
        assert b.post('/api/recollection/finish',json={'session_id':sid}).status_code==404
        a.post('/api/recollection/finish',json={'session_id':sid})
        assert b.get('/api/recollection').json()['entries']==[]
        assert a.post('/api/recollection/settings',json={'enabled':False}).json()['enabled'] is False
        next_id=begin(a)
        assert a.post('/api/recollection/finish',json={'session_id':next_id}).json()['recollection'] is None
        assert len(a.get('/api/recollection').json()['entries'])==1
        assert a.delete('/api/recollection').json()['entries']==[]
        assert begin(a)

def test_draft_or_empty_plan_cannot_be_remembered_as_completed(tmp_path):
    with TestClient(create_app(configured(tmp_path/'empty.sqlite'))) as c:
        sid=c.post('/api/session',json={}).json()['session_id']
        assert c.post('/api/recollection/finish',json={'session_id':sid}).status_code==409
        assert c.get('/api/recollection').json()['latest'] is None
