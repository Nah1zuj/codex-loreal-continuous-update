from concurrent.futures import ThreadPoolExecutor
import sqlite3

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def reflect(client):
    response = client.post('/api/experience/reflect', json={})
    assert response.status_code == 200, response.text
    return response.json()['session']


def command(session, event, action='advance'):
    plan = session['makeup_plan']
    return {'session_id': session['session_id'], 'action': action, 'event_id': event,
            'expected_plan_id': plan['id'], 'expected_revision': plan['revision'],
            'expected_step_id': plan['steps'][plan['active_index']]['id']}


def test_concurrent_commands_and_restart_keep_one_committed_result(tmp_path):
    settings = Settings(memory_path=tmp_path / 'commands.sqlite')
    with TestClient(create_app(settings)) as owner:
        session = reflect(owner)
        request = command(session, 'advance-once')
        other = {**request, 'event_id': 'other-advance'}
        with ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(
                lambda data: owner.post('/api/makeup/command', json=data),
                [request, request, other],
            ))
        assert sorted(r.status_code for r in results).count(409) >= 1
        # Either event can win the race. Only its requests can replay successfully.
        committed = next(r.json()['event'] for r in results if r.status_code == 200)
        current = owner.get('/api/session/' + session['session_id']).json()
        assert current['makeup_plan']['active_index'] == 1
        assert current['makeup_plan']['revision'] == session['makeup_plan']['revision'] + 1
        assert committed['revision'] == current['makeup_plan']['revision']
        winner = request if committed['event_id'] == request['event_id'] else other
        replay = owner.post('/api/makeup/command', json=winner).json()
        assert replay['duplicate'] is True and replay['event'] == committed
        mismatch = owner.post('/api/makeup/command', json={**winner, 'action': 'skip'})
        assert mismatch.status_code == 409 and mismatch.json()['code'] == 'EVENT_MISMATCH'
        cookies = dict(owner.cookies)
    with TestClient(create_app(settings)) as restarted, TestClient(create_app(settings)) as stranger:
        restarted.cookies.update(cookies)
        path = '/api/makeup/events/' + session['session_id'] + '/' + committed['event_id']
        assert restarted.get(path).json()['event'] == committed
        assert stranger.get(path).status_code == 404


def test_compatible_entrypoints_share_event_and_read_only_commands_preserve_version(tmp_path):
    with TestClient(create_app(Settings(memory_path=tmp_path / 'compat.sqlite'))) as client:
        session = reflect(client)
        sid = session['session_id']
        data = command(session, 'legacy-advance')
        legacy = {key: value for key, value in data.items() if key != 'action'}
        response = client.post('/api/routine/advance', json=legacy)
        assert response.status_code == 200, response.text
        advanced = response.json()
        replay = client.post('/api/makeup/command', json=data).json()
        assert replay['event'] == advanced['event'] and replay['duplicate'] is True
        assert replay['session']['makeup_plan']['active_index'] == 1
        repeated = client.post('/api/chat', json={'session_id': sid, 'message': '重复'}).json()
        assert repeated['session']['makeup_plan']['revision'] == advanced['event']['revision']


def test_skip_pause_restore_and_finish_leave_factual_steps(tmp_path):
    app = create_app(Settings(memory_path=tmp_path / 'controls.sqlite'))
    with TestClient(app) as client, TestClient(app) as stranger:
        session = reflect(client)
        sid = session['session_id']
        assert stranger.post('/api/session/' + sid + '/restore').status_code == 404
        check = client.post('/api/chat', json={'session_id': sid, 'message': 'check this'})
        assert check.status_code == 200
        grant = client.post('/api/chat', json={'session_id': sid, 'action': 'camera_consent', 'consent': True})
        assert grant.json()['session']['camera_consent'] is True
        restore = client.post('/api/session/' + sid + '/restore').json()
        assert restore['camera_consent'] is False
        assert restore['makeup_plan']['revision'] == session['makeup_plan']['revision']
        skipped = client.post('/api/makeup/command', json=command(restore, 'skip', 'skip')).json()
        assert skipped['session']['makeup_plan']['steps'][0]['status'] == 'skipped'
        paused = client.post('/api/makeup/command', json=command(skipped['session'], 'pause', 'pause')).json()
        assert paused['session']['makeup_plan']['workflow'] == 'PAUSED'
        invalid = client.post('/api/makeup/command', json=command(paused['session'], 'invalid'))
        assert invalid.status_code == 409
        resume = client.post('/api/makeup/command', json=command(paused['session'], 'resume', 'resume')).json()
        assert resume['session']['makeup_plan']['active_index'] == 1
        assert resume['session']['camera_consent'] is False
        done = client.post('/api/makeup/command', json=command(resume['session'], 'finish', 'finish')).json()
        assert done['summary']['completed_steps'] == []
        assert done['session']['makeup_plan']['steps'][0]['status'] == 'skipped'
        reflect_again = client.post('/api/experience/reflect', json={'session_id': sid}).json()
        assert reflect_again['session']['session_id'] == sid
        assert reflect_again['session']['makeup_plan']['id'] == done['session']['makeup_plan']['id']


def test_migration_keeps_legacy_event(tmp_path):
    path = tmp_path / 'legacy.sqlite'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE makeup_events (session_id TEXT,event_id TEXT,intent TEXT,PRIMARY KEY(session_id,event_id))')
        db.execute('INSERT INTO makeup_events VALUES (?,?,?)', ('legacy', 'evt', 'start'))
    for _ in range(2):
        create_app(Settings(memory_path=path))
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT * FROM makeup_events').fetchone() == ('legacy', 'evt', 'start')
        assert db.execute('SELECT COUNT(*) FROM schema_migrations WHERE version=3').fetchone() == (1,)
        # The pre-migration writer can still insert three values and delete old events.
        db.execute('INSERT INTO makeup_events VALUES (?,?,?)', ('legacy', 'original-writer', 'advance'))
        db.execute('INSERT INTO makeup_event_receipts VALUES (?,?,?)', ('legacy', 'original-writer', '{}'))
        db.execute('DELETE FROM makeup_events WHERE session_id=?', ('legacy',))
        assert db.execute('SELECT COUNT(*) FROM makeup_event_receipts').fetchone() == (0,)


def test_stream_end_session_is_separate_from_pausing_teaching(tmp_path):
    with TestClient(create_app(Settings(memory_path=tmp_path / 'stream-end.sqlite'))) as client:
        session = reflect(client)
        sid = session['session_id']
        question = client.post('/api/chat', json={'session_id': sid, 'message': '下一步呢？'}).json()
        assert question['session']['makeup_plan']['active_index'] == 0
        stream = client.post('/api/chat/stream', json={'session_id': sid, 'message': 'stop session',
                                                      'event_id': 'stop-via-stream'})
        assert '"type": "committed"' in stream.text
        current = client.get('/api/session/' + sid).json()
        assert current['stage'] == 'COMPLETE'
        assert current['makeup_plan']['status'] == 'completed'
        assert all(step['status'] != 'completed' for step in current['makeup_plan']['steps'])
