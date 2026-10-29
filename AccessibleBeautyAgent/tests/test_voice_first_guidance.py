import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app

@pytest.mark.parametrize('message',['我想开始步骤','开始化妆吧','请带我一步一步做','I want to start the steps'])
def test_natural_start_begins_without_reselecting(tmp_path,message):
    with TestClient(create_app(Settings(memory_path=tmp_path/'guide.sqlite'))) as client:
        selected=client.post('/api/chat',json={'message':'日常自然妆'}).json()
        reply=client.post('/api/chat',json={'session_id':selected['session']['session_id'],'message':message}).json()
        assert reply['session']['stage']=='GUIDE'
        assert reply['session']['routine_step']==0 and reply['step']['instruction']
        again=client.post('/api/chat',json={'session_id':reply['session']['session_id'],'message':message}).json()
        assert again['session']['routine_step']==0 and again['step']==reply['step']


def test_step_question_reaches_coach_without_advancing_or_claiming_sight(tmp_path):
    app=create_app(Settings(memory_path=tmp_path/'coach.sqlite'))
    class Coach:
        def guide(self,question,step,locale):
            assert question=='我不知道这一步怎么涂'
            assert step['instruction'] and locale=='zh-CN'
            return '先暂停在这一小步。你想听慢一点的说明吗？'
    with TestClient(app) as client:
        selected=client.post('/api/chat',json={'message':'日常自然妆'}).json()
        sid=selected['session']['session_id']
        client.post('/api/chat',json={'session_id':sid,'message':'开始步骤'})
        app.state.agent.language=Coach()
        reply=client.post('/api/chat',json={'session_id':sid,'message':'我不知道这一步怎么涂'}).json()
        assert reply['message']=='先暂停在这一小步。你想听慢一点的说明吗？'
        assert reply['session']['stage']=='GUIDE' and reply['session']['routine_step']==0


def test_deepseek_coaching_context_excludes_session_and_requires_single_step():
    from app.agent.providers import DeepSeekLanguageProvider
    provider=DeepSeekLanguageProvider(Settings())
    class Transport:
        def chat_json(self,model,system,content):
            assert 'one small action' in system and 'No image has been provided' in system
            assert 'instruction' in content and 'session_id' not in content
            return {'message':'Pause here. Which part feels unclear?'}
    provider.client=Transport()
    assert provider.guide('How?',{'instruction':'Use familiar prep'},'en')=='Pause here. Which part feels unclear?'

def test_natural_next_confirmation_advances_one_step(tmp_path):
    with TestClient(create_app(Settings(memory_path=tmp_path/'next.sqlite'))) as client:
        first=client.post('/api/chat',json={'message':'日常自然妆'}).json()
        sid=first['session']['session_id']
        client.post('/api/chat',json={'session_id':sid,'message':'开始步骤'})
        reply=client.post('/api/chat',json={'session_id':sid,'message':'我想开始下一步'}).json()
        assert reply['session']['routine_step']==1 and reply['step']['instruction']

def test_coach_receives_previous_question_to_interpret_a_short_answer(tmp_path):
    app=create_app(Settings(memory_path=tmp_path/'followup.sqlite'))
    class Coach:
        def guide(self,question,step,locale):
            if question=='粉底液':
                assert step['previous_reply']=='你手边是粉底液还是气垫？'
                return '先取少量你熟悉的粉底液，停在这一步。'
            return '你手边是粉底液还是气垫？'
    with TestClient(app) as client:
        sid=client.post('/api/chat',json={'message':'日常自然妆'}).json()['session']['session_id']
        client.post('/api/chat',json={'session_id':sid,'message':'开始步骤'})
        app.state.agent.language=Coach()
        client.post('/api/chat',json={'session_id':sid,'message':'我该用什么？'})
        reply=client.post('/api/chat',json={'session_id':sid,'message':'粉底液'}).json()
        assert reply['session']['routine_step']==0
        assert '先取少量' in reply['message']
