import json
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings

def parsed(response):
    assert response.status_code==200,response.text
    rows=[json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert rows[-1]['type']=='final',rows
    return rows[-1]['reply']

def test_exact_text_scenario_owner_consent_and_recovery(tmp_path):
    settings=Settings(memory_path=tmp_path/'flow.sqlite')
    app=create_app(settings)
    with TestClient(app) as c:
        reply=parsed(c.post('/api/chat/stream',json={'message':'你好，我今天想画一个自然的日常妆，大概十五分钟。'}))
        sid=reply['session']['session_id']
        def say(text,event=None):return parsed(c.post('/api/chat/stream',json={'session_id':sid,'message':text,'event_id':event}))
        assert reply['session']['makeup_plan']['status']=='draft'
        assert say('好的，开始。')['step']['step_id']=='coaching_prep_zh'
        assert say('我已经做好了，下一步呢？','one')['step']['step_id']=='coaching_foundation_zh'
        assert say('我已经做好了，下一步呢？','one')['step']['step_id']=='coaching_foundation_zh'
        say('等一下，我不太明白怎么上底妆。')
        assert say('你能再说一遍吗？')['step']['step_id']=='coaching_foundation_zh'
        assert say('好，我完成了。')['step']['step_id']=='coaching_blush_zh'
        say('我现在开始画腮红。')
        reply=say('你帮我看看左右是不是一样。')
        assert reply['session']['camera_consent'] is False
        assert reply['session']['visual_state'] is None
        say('现在我调整好了。')
        reply=say('好的，今天完成了。')
        assert reply['session']['makeup_plan']['status']=='completed'
        assert c.get('/api/journal').json()['entries']==[]
        reply=say('保存到我的记录。')
        jid=reply['session']['makeup_plan']['saved_journal_id'];assert jid
        say('保存到我的记录。')
        entries=c.get('/api/journal').json()['entries'];assert len(entries)==1
        assert entries[0]['coaching_summary']['completed_steps']==['准备与补水','轻薄底妆']
        assert entries[0]['coaching_summary']['observations'] is None
        cookies=c.cookies
    with TestClient(create_app(settings)) as recovered:
        recovered.cookies.update(cookies)
        assert recovered.get('/api/session/'+sid).status_code==200
    with TestClient(create_app(settings)) as stranger:
        assert stranger.get('/api/session/'+sid).status_code==404

def test_live_transport_not_short_circuited_and_context_preserved(tmp_path,monkeypatch):
    from app.agent import conversation
    seen=[]
    class Transport:
        def __init__(self,*args):pass
        async def stream_chat(self,model,messages,tools=None):
            seen.append(messages[0]['content'])
            yield {'choices':[{'delta':{'content':'One manageable action, grounded in the current step.'}}]}
    monkeypatch.setattr(conversation,'RemoteModelClient',Transport)
    app=create_app(Settings(memory_path=tmp_path/'flow.sqlite'));app.state.agent.settings.model_provider='deepseek'
    with TestClient(app) as c:
        sid=parsed(c.post('/api/chat/stream',json={'message':'I want natural makeup','locale':'en'}))['session']['session_id']
        for text in ['start','next','Tell me about rain','repeat']:
            reply=parsed(c.post('/api/chat/stream',json={'session_id':sid,'message':text,'locale':'en'}))
        assert reply['step']['step_id']=='coaching_foundation_en'
        assert len(seen)==5 and all('COACHING_OPERATION=' in p for p in seen)
        assert 'Reply as plain text entirely in English' in seen[-1]

def test_committed_step_is_streamed_even_when_model_fails(tmp_path,monkeypatch):
    from app.agent import conversation
    class Transport:
        def __init__(self,*args):pass
        async def stream_chat(self,*args):
            raise RuntimeError('offline')
            yield
    app=create_app(Settings(memory_path=tmp_path/'flow.sqlite'))
    with TestClient(app) as c:
        reply=parsed(c.post('/api/chat/stream',json={'message':'I want makeup','locale':'en'}));sid=reply['session']['session_id']
        parsed(c.post('/api/chat/stream',json={'message':'start','session_id':sid,'locale':'en'}))
        app.state.agent.settings.model_provider='deepseek';monkeypatch.setattr(conversation,'RemoteModelClient',Transport)
        response=c.post('/api/chat/stream',json={'message':'next','session_id':sid,'locale':'en'})
        rows=[json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
        assert rows[-1]['type']=='error'
        assert [r for r in rows if r['type']=='session'][-1]['session']['makeup_plan']['active_index']==1
        assert c.get('/api/makeup/'+sid).json()['plan']['active_index']==1

def test_failed_retrieval_and_stale_event_preserve_plan(tmp_path,monkeypatch):
    a=create_app(Settings(memory_path=tmp_path/'flow.sqlite')).state.agent;s=a.sessions.create('owner')
    a.coaching.create(s,{});a.coaching.act(s,'start','a')
    with pytest.raises(ValueError):a.coaching.act(s,'advance','b','wrong-step')
    assert s.makeup_plan.active_index==0
    monkeypatch.setattr(a.coaching,'knowledge',lambda *args:[])
    t=a.sessions.create('owner')
    with pytest.raises(ValueError):a.coaching.create(t,{})
    assert t.makeup_plan is None

def test_tools_validate_and_cannot_save_without_confirmation(tmp_path):
    from app.agent.tools import ToolRegistry
    a=create_app(Settings(memory_path=tmp_path/'flow.sqlite')).state.agent;s=a.sessions.create('owner')
    tools=ToolRegistry(a)
    assert tools.execute(s,'create_makeup_plan',{'needs':{'minutes':-1}},'想化妆')['ok'] is False
    assert tools.execute(s,'save_confirmed_beauty_journal',{},'聊天')['ok'] is False
    a.coaching.create(s,{});a.coaching.act(s,'start','a')
    assert tools.execute(s,'advance_makeup_step',{},'等等，我还没画完')['ok'] is False
    assert tools.execute(s,'search_reviewed_makeup_knowledge',{'query':'blush'})['result']['reviewed_available'] is False

def test_journal_requires_presented_summary_and_plan_deletion_is_owned(tmp_path):
    app=create_app(Settings(memory_path=tmp_path/'flow.sqlite'));a=app.state.agent
    s=a.sessions.create('owner');a.coaching.create(s,{});a.coaching.act(s,'start','a');a.coaching.act(s,'finish','b')
    with pytest.raises(PermissionError):a.coaching.save(s,'保存到我的记录。')
    with TestClient(app) as c:
        sid=parsed(c.post('/api/chat/stream',json={'message':'I want beginner makeup','locale':'en'}))['session']['session_id']
        assert c.get('/api/makeup/'+sid).json()['plan']['status']=='draft'
        assert c.request('DELETE','/api/makeup/'+sid,json={'explicit_consent':False}).status_code==403
        assert c.request('DELETE','/api/makeup/'+sid,json={'explicit_consent':True}).json()['deleted'] is True
