import json
import time

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def configured(path):
    return Settings(memory_path=path, model_provider='mock', vision_provider='mock',
                    embedding_provider='mock', reading_provider='mock',
                    reference_provider='mock', allow_remote_ai=False)


def begin(client):
    reply = client.post('/api/experience/reflect', json={})
    assert reply.status_code == 200, reply.text
    return reply.json()['session']['session_id']


def test_finish_returns_facts_without_saving_an_unconfirmed_summary(tmp_path):
    path = tmp_path / 'recollection.sqlite'
    with TestClient(create_app(configured(path))) as client:
        sid = begin(client)
        for _ in range(2):
            reply = client.post('/api/recollection/finish', json={'session_id': sid})
            assert reply.status_code == 200
            body = reply.json()
            assert body['summary']['completed_steps'] == []
            assert body['summary']['requires_confirmation'] is True
            assert body['recollection'] is None
            assert '下次见面' not in body['message']
        cookies = dict(client.cookies)
    with TestClient(create_app(configured(path))) as returning:
        returning.cookies.update(cookies)
        assert returning.get('/api/recollection').json()['entries'] == []
        with returning.app.state.agent.memory.connect() as db:
            assert db.execute('SELECT COUNT(*) FROM look_recollections').fetchone()[0] == 0
            assert db.execute('SELECT COUNT(*) FROM memories').fetchone()[0] == 0
            assert db.execute('SELECT COUNT(*) FROM journal').fetchone()[0] == 0


def test_text_finish_does_not_save_and_question_does_not_confirm_journal(tmp_path):
    app = create_app(configured(tmp_path / 'text.sqlite'))
    with TestClient(app) as client:
        sid = begin(client)
        finish = client.post('/api/chat', json={'session_id': sid, 'message': '结束今天'})
        assert finish.status_code == 200
        assert finish.json()['session']['makeup_plan']['status'] == 'completed'
        response = client.post('/api/chat', json={'session_id': sid, 'message': '如何保存到我的记录？'})
        assert response.status_code == 200
        assert client.get('/api/journal').json()['entries'] == []
        assert client.get('/api/recollection').json()['entries'] == []


def test_legacy_summary_is_owner_scoped_and_excluded_from_reuse(tmp_path):
    app = create_app(configured(tmp_path / 'owners.sqlite'))
    with TestClient(app) as owner, TestClient(app) as other:
        sid = begin(owner)
        user_id = app.state.agent.sessions.get(sid).user_id
        payload = {'session_id': sid, 'name': 'Old look', 'date': '2026-11-07',
                   'occasion': 'daily', 'style': 'evening', 'completed_steps': [],
                   'all_steps_completed': False, 'record_kind': 'look_summary'}
        with app.state.agent.memory.connect() as db:
            db.execute('INSERT INTO look_recollections VALUES (?,?,?,?)',
                       (sid, user_id, json.dumps(payload), time.time()))
        assert other.post('/api/recollection/finish', json={'session_id': sid}).status_code == 404
        assert other.get('/api/recollection').json()['entries'] == []
        view = owner.get('/api/recollection').json()
        assert view['latest'] is None
        assert view['entries'][0]['origin'] == 'legacy_automatic'
        assert owner.post('/api/recollection/settings', json={'enabled': False}).json()['enabled'] is False
        reuse = owner.post('/api/experience/reflect', json={'reuse_previous': True})
        assert reuse.json()['session']['makeup_plan']['needs']['style'] == 'natural'
        assert owner.delete('/api/recollection').json()['entries'] == []


def test_draft_or_empty_plan_cannot_be_remembered_as_completed(tmp_path):
    with TestClient(create_app(configured(tmp_path / 'empty.sqlite'))) as client:
        sid = client.post('/api/session', json={}).json()['session_id']
        assert client.post('/api/recollection/finish', json={'session_id': sid}).status_code == 409
        assert client.get('/api/recollection').json()['latest'] is None
