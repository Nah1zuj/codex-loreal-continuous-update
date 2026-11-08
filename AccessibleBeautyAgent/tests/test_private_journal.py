from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings

def test_private_journal_requires_consent_and_keeps_owner(tmp_path):
    with TestClient(create_app(Settings(memory_path=tmp_path/'journal.sqlite'))) as client:
        entry={'date':'2026-10-12','look':'日常','feeling':'轻松','reflection':'测试记录','traits':'我喜欢自然','explicit_consent':False,'user_id':'owner'}
        assert client.post('/api/journal',json=entry).status_code==403
        assert client.get('/api/journal?user_id=owner').json()['entries']==[]
        entry['explicit_consent']=True
        row=client.post('/api/journal',json=entry).json()
        assert row['look']=='日常'
        assert len(client.get('/api/journal?user_id=owner').json()['entries'])==1
        assert client.get('/api/journal?user_id=other').json()['entries']==[]
        assert client.request('DELETE','/api/journal/'+row['id'],json={'user_id':'other','explicit_consent':True}).status_code==404
        assert client.request('DELETE','/api/journal/'+row['id'],json={'user_id':'owner','explicit_consent':False}).status_code==403
        assert client.request('DELETE','/api/journal/'+row['id'],json={'user_id':'owner','explicit_consent':True}).status_code==200
        assert client.post('/api/journal',json={**entry,'explicit_consent':'true'}).status_code==422
        assert client.post('/api/journal',json={**entry,'photo':'not-supported'}).status_code==422
