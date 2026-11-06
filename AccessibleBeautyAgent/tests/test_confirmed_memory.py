from concurrent.futures import ThreadPoolExecutor
import json
import time

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.memory.migrations import RETENTION_SECONDS


def finish(client):
    sid=client.post('/api/experience/reflect',json={}).json()['session']['session_id']
    response=client.post('/api/recollection/finish',json={'session_id':sid})
    response.raise_for_status()
    return sid,response.json()['summary_candidate']


def endpoint(candidate,action):
    return '/api/recollection/candidates/'+candidate['candidate_id']+'/'+action


def save_preference(client,candidate):
    draft=client.post('/api/memory/preview',json={'user_id':'demo','candidate':candidate}).json()
    return client.post('/api/memory',json={'user_id':'demo',**draft,'explicit_consent':True})


def test_exact_summary_version_is_confirmed_once_and_cannot_be_replayed_after_delete(tmp_path):
    app=create_app(Settings(memory_path=tmp_path/'summaries.sqlite'))
    with TestClient(app) as owner,TestClient(app) as stranger:
        sid,candidate=finish(owner)
        assert owner.get('/api/recollection').json()['entries']==[]
        assert stranger.get('/api/recollection/candidate/'+sid).status_code==404
        edits={'name':'Reviewed title','note':'A private note'}
        newer=owner.post(endpoint(candidate,'preview'),json=edits).json()
        assert newer['version']!=candidate['version']
        body={'version':newer['version'],'edits':edits,'explicit_consent':True}
        assert owner.post(endpoint(candidate,'confirm'),json={**body,'version':candidate['version']}).status_code==409
        assert owner.post(endpoint(candidate,'confirm'),json={**body,'explicit_consent':False}).status_code==403
        assert stranger.post(endpoint(candidate,'confirm'),json=body).status_code==404
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:owner.post(endpoint(candidate,'confirm'),json=body),range(2)))
        assert sorted(r.json()['duplicate'] for r in results)==[False,True]
        assert results[0].json()['record']==results[1].json()['record']
        record=results[0].json()['record']
        assert record['note']=='A private note' and record['completed_steps']==[]
        assert owner.post(endpoint(candidate,'confirm'),json={**body,'edits':{}}).status_code==409
        assert '_confirmed_edits_digest' not in record
        assert owner.get('/api/recollection').json()['latest'] is None
        assert owner.get('/api/journal').json()['entries']==[]
        assert owner.get('/api/recollection/candidate/'+sid).status_code==404
        assert owner.post('/api/recollection/'+record['id']+'/reuse',json={'explicit_consent':True}).json()['latest']['id']==record['id']
        assert stranger.request('DELETE','/api/recollection/'+record['id'],json={'explicit_consent':True}).status_code==404
        deleted=owner.request('DELETE','/api/recollection/'+record['id'],json={'explicit_consent':True}).json()
        assert deleted['entries']==[] and deleted['latest'] is None
        assert owner.post(endpoint(candidate,'confirm'),json=body).status_code==404
        with app.state.agent.memory.connect() as db:
            assert db.execute('SELECT COUNT(*) FROM confirmed_summaries').fetchone()[0]==0


def test_decline_creates_no_summary_and_migrated_legacy_can_be_explicitly_reused(tmp_path):
    app=create_app(Settings(memory_path=tmp_path/'legacy.sqlite'))
    with TestClient(app) as client:
        sid,candidate=finish(client)
        assert client.post(endpoint(candidate,'reject'),json={'version':candidate['version']}).json()=={'saved':False,'rejected':True}
        assert client.get('/api/recollection/candidate/'+sid).status_code==404
        assert client.post(endpoint(candidate,'confirm'),json={'version':candidate['version'],'explicit_consent':True}).status_code==404
        owner=app.state.agent.sessions.get(sid).user_id
        legacy={'session_id':'old-1','name':'Legacy private title','style':'evening','date':'2026-11-01','completed_steps':[]}
        with app.state.agent.memory.connect() as db:
            db.execute('INSERT INTO look_recollections VALUES (?,?,?,?)',('old-1',owner,json.dumps(legacy),time.time()))
        view=client.get('/api/recollection').json()
        assert view['latest'] is None and view['entries'][0]['origin']=='legacy_automatic'
        old=client.post('/api/recollection/candidates/legacy:old-1/preview',json={}).json()
        row=client.post(endpoint(old,'confirm'),json={'version':old['version'],'explicit_consent':True}).json()['record']
        assert row['origin']=='legacy_reconfirmed'
        assert client.post('/api/recollection/'+row['id']+'/reuse',json={'explicit_consent':True}).status_code==200
        plan=client.post('/api/experience/reflect',json={'reuse_previous':True}).json()['session']['makeup_plan']
        assert plan['needs']['style']=='evening'
        assert 'Legacy private title' not in json.dumps(plan)
        client.request('DELETE','/api/recollection/'+row['id'],json={'explicit_consent':True}).raise_for_status()
        plan=client.post('/api/experience/reflect',json={'reuse_previous':True}).json()['session']['makeup_plan']
        assert plan['needs']['style']=='natural'
        with app.state.agent.memory.connect() as db:
            assert db.execute('SELECT COUNT(*) FROM look_recollections').fetchone()[0]==0


def test_expiration_cleans_progress_events_and_summary_without_journal_or_preferences(tmp_path):
    app=create_app(Settings(memory_path=tmp_path/'retention.sqlite'))
    with TestClient(app) as client:
        sid,candidate=finish(client)
        client.post(endpoint(candidate,'confirm'),json={'version':candidate['version'],'explicit_consent':True}).raise_for_status()
        client.post('/api/journal',json={'date':'2026-11-01','look':'Separate journal','explicit_consent':True}).raise_for_status()
        save_preference(client,{'feedback':'Separate preference'}).raise_for_status()
        with app.state.agent.memory.connect() as db:
            db.execute('UPDATE makeup_sessions SET updated_at=? WHERE session_id=?',(time.time()-RETENTION_SECONDS-1,sid))
            db.execute('UPDATE confirmed_summaries SET expires_at=?',(time.time()-1,))
        assert client.get('/api/recollection').json()['entries']==[]
        assert len(client.get('/api/journal').json()['entries'])==1
        assert len(client.get('/api/profile/demo').json()['episodes'])==1
        with app.state.agent.memory.connect() as db:
            assert db.execute('SELECT COUNT(*) FROM makeup_sessions WHERE session_id=?',(sid,)).fetchone()[0]==0
            assert db.execute('SELECT COUNT(*) FROM makeup_events WHERE session_id=?',(sid,)).fetchone()[0]==0
            assert db.execute('SELECT COUNT(*) FROM makeup_event_receipts WHERE session_id=?',(sid,)).fetchone()[0]==0


def test_independent_journal_idempotent_save_versioned_edit_and_delete(tmp_path):
    with TestClient(create_app(Settings(memory_path=tmp_path/'journal.sqlite'))) as owner,          TestClient(create_app(Settings(memory_path=tmp_path/'journal.sqlite'))) as stranger:
        original={'date':'2026-11-01','look':'Independent','reflection':'First version',
                  'explicit_consent':True,'confirmation_id':'same-draft'}
        first=owner.post('/api/journal',json=original).json()
        assert owner.post('/api/journal',json=original).json()==first
        assert owner.post('/api/journal',json={**original,'reflection':'Unreviewed edit'}).status_code==409
        path='/api/journal/'+first['id']
        edit={'date':'2026-11-01','look':'Independent','reflection':'Confirmed revision',
              'explicit_consent':True,'expected_version':1}
        assert stranger.post(path+'/edit',json=edit).status_code==404
        changed=owner.post(path+'/edit',json=edit)
        assert changed.status_code==200 and changed.json()['version']==2
        assert owner.post(path+'/edit',json=edit).status_code==409
        assert owner.post('/api/journal',json=original).status_code==409
        assert owner.get('/api/journal').json()['entries'][0]['reflection']=='Confirmed revision'
        assert owner.request('DELETE',path,json={'explicit_consent':True}).status_code==200
        assert owner.get('/api/journal').json()['entries']==[]
        assert owner.post('/api/journal',json=original).status_code==409


def test_preference_deletion_removes_derived_legacy_copies_and_future_context(tmp_path):
    app=create_app(Settings(memory_path=tmp_path/'delete.sqlite'))
    with TestClient(app) as client:
        sid=client.post('/api/chat',json={'message':'日常'}).json()['session']['session_id']
        agent=app.state.agent
        session=agent.sessions.get(sid)
        saved=save_preference(client,{'feedback':'Sensitive test preference','preferred_finish':['secret']}).json()
        summary={'preferences':{'preferred_finish':['secret']},'completed_steps':[]}
        agent.journal.save(session.user_id,{'look':'Earlier copy','coaching_summary':summary,'reflection':json.dumps(summary)})
        app.state.conversation.append(sid,'agent','A secret preference','en')
        assert client.delete('/api/memory/'+saved['memory_id'],params={'user_id':'demo','explicit_consent':True}).status_code==200
        assert client.get('/api/profile/demo').json()['profile']['preferred_finish']==[]
        assert app.state.conversation.history(sid)==[]
        assert 'secret' not in json.dumps(client.get('/api/journal').json())


def test_preference_preview_is_owner_scoped_versioned_and_durably_idempotent(tmp_path):
    settings=Settings(memory_path=tmp_path/'preferences.sqlite')
    with TestClient(create_app(settings)) as owner,TestClient(create_app(settings)) as stranger:
        bare={'user_id':'demo','candidate':{'feedback':'Private preference'},'explicit_consent':True}
        assert owner.post('/api/memory',json=bare).status_code==409
        draft=owner.post('/api/memory/preview',json=bare).json()
        confirm={'user_id':'demo',**draft,'explicit_consent':True}
        assert owner.post('/api/memory',json={**confirm,'candidate':{'feedback':'Different'}}).status_code==409
        assert stranger.post('/api/memory',json=confirm).status_code==409
        saved=owner.post('/api/memory',json=confirm).json()
        assert saved['saved'] is True and saved['duplicate'] is False
        cookie=dict(owner.cookies)
    with TestClient(create_app(settings)) as restarted:
        restarted.cookies.update(cookie)
        repeated=restarted.post('/api/memory',json=confirm).json()
        assert repeated['memory_id']==saved['memory_id'] and repeated['duplicate'] is True
        assert len(restarted.get('/api/profile/demo').json()['episodes'])==1
        restarted.delete('/api/memory/'+saved['memory_id'],params={'user_id':'demo','explicit_consent':True}).raise_for_status()
        assert restarted.post('/api/memory',json=confirm).status_code==409


def test_session_preference_requires_the_returned_candidate_and_is_idempotent(tmp_path):
    with TestClient(create_app(Settings(memory_path=tmp_path/'session-preference.sqlite'))) as client:
        sid=client.post('/api/experience/reflect',json={}).json()['session']['session_id']
        client.post('/api/recollection/finish',json={'session_id':sid}).raise_for_status()
        # Direct feedback is only accepted once the course is finished.
        client.post('/api/feedback',json={'session_id':sid,'feedback':'偏好自然色'}).raise_for_status()
        session=client.get('/api/session/'+sid).json()
        body={'session_id':sid,'action':'memory_consent','consent':True,
              'memory_candidate_id':session['memory_candidate_id'],
              'memory_candidate_version':session['memory_candidate_version']}
        assert client.post('/api/chat',json={**body,'memory_candidate_version':'0'*64}).status_code==409
        assert client.get('/api/profile/demo').json()['episodes']==[]
        client.post('/api/chat',json=body).raise_for_status()
        client.post('/api/chat',json=body).raise_for_status()
        assert len(client.get('/api/profile/demo').json()['episodes'])==1
        assert client.get('/api/recollection').json()['entries']==[]


def test_legacy_journal_save_retries_are_idempotent_without_blocking_new_explicit_entry(tmp_path):
    with TestClient(create_app(Settings(memory_path=tmp_path/'legacy-journal.sqlite'))) as client:
        value={'date':'2026-11-07','look':'Daily','explicit_consent':True}
        first=client.post('/api/journal',json=value).json()
        assert client.post('/api/journal',json=value).json()==first
        assert client.request('DELETE','/api/journal/'+first['id'],json={'explicit_consent':True}).status_code==200
        assert client.post('/api/journal',json=value).status_code==409
        assert client.post('/api/journal',json={**value,'confirmation_id':'new-reviewed-entry'}).json()['id']!=first['id']


def test_same_browser_alias_keeps_summary_visible_to_its_own_namespace(tmp_path):
    app=create_app(Settings(memory_path=tmp_path/'alias.sqlite'))
    with TestClient(app) as owner,TestClient(app) as stranger:
        sid=owner.post('/api/chat/stream',json={'user_id':'alternate','message':'我想画自然妆'}).text.split('"session_id": "')[1].split('"')[0]
        owner.post('/api/experience/reflect',json={'session_id':sid}).raise_for_status()
        finished=owner.post('/api/recollection/finish',json={'session_id':sid}).json()
        candidate=finished['summary_candidate']
        assert owner.get('/api/recollection/candidate/'+sid).json()==candidate
        assert stranger.get('/api/recollection/candidate/'+sid).status_code==404
        saved=owner.post(endpoint(candidate,'confirm'),json={'version':candidate['version'],'explicit_consent':True}).json()
        assert saved['record']['session_id']==sid
        assert owner.get('/api/recollection').json()['entries']==[]
        assert owner.get('/api/recollection?user_id=alternate').json()['entries'][0]['id']==saved['record']['id']
        assert stranger.get('/api/recollection?user_id=alternate').json()['entries']==[]
