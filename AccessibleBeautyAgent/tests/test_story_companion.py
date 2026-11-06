from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings

def test_story_without_occasion_gets_conversation_not_a_menu(tmp_path):
    with TestClient(create_app(Settings(memory_path=tmp_path/'story.sqlite'))) as client:
        response=client.post('/api/chat',json={'message':'今天有点累，我想聊聊我的一天'}).json()
        assert '晚宴、演讲' not in response['message']
        assert '今天' in response['message']
        assert response['session']['routine_started'] is False

def test_forest_story_becomes_optional_creative_direction(tmp_path):
    with TestClient(create_app(Settings(memory_path=tmp_path/'forest.sqlite'))) as client:
        response=client.post('/api/chat',json={'message':'我的日常妆想要树林的感觉'}).json()
        assert '苔绿' in response['message'] and '眼影' in response['message']
        assert not response['session']['routine_started']

def test_automatic_journal_draft_does_not_persist(tmp_path):
    with TestClient(create_app(Settings(memory_path=tmp_path/'draft.sqlite'))) as client:
        response=client.post('/api/journal/draft',json={'messages':[{'role':'user','text':'今天想要日常树林妆，感觉放松'},{'role':'agent','text':'我们可以试试苔绿。'}],'locale':'zh-CN'})
        assert response.status_code==200
        draft=response.json()
        assert '树林' in draft['reflection'] and draft['traits']==''
        assert client.get('/api/journal').json()['entries']==[]
        assert client.post('/api/journal/draft',json={'messages':[{'role':'system','text':'x'}]}).status_code==422

def test_category_recommendations_keep_the_current_step(tmp_path):
    with TestClient(create_app(Settings(memory_path=tmp_path/'category.sqlite'))) as client:
        sid=client.post('/api/chat',json={'message':'日常自然妆'}).json()['session']['session_id']
        client.post('/api/chat',json={'session_id':sid,'message':'开始步骤'})
        reply=client.post('/api/chat',json={'session_id':sid,'message':'欧莱雅全品类推荐，衣服材质和香氛呢？'}).json()
        assert '护发' in reply['message'] and '材质' in reply['message']
        assert reply['session']['routine_step']==0

def test_begin_after_an_open_story_starts_the_first_step(tmp_path):
    with TestClient(create_app(Settings(memory_path=tmp_path/'begin.sqlite'))) as client:
        sid=client.post('/api/chat',json={'message':'我今天想聊聊天'}).json()['session']['session_id']
        reply=client.post('/api/chat',json={'session_id':sid,'message':'我想开始下一步'}).json()
        assert reply['session']['stage']=='GUIDE' and reply['session']['routine_step']==0
        assert reply['step']['instruction']

def test_model_draft_is_bounded_and_not_a_storage_or_personality_instruction():
    from app.agent.providers import DeepSeekLanguageProvider
    provider=DeepSeekLanguageProvider(Settings())
    class Transport:
        def chat_json(self,model,policy,content):
            assert 'explicitly stated by the USER' in policy and 'Never infer personality' in policy
            assert 'No storage is performed' in policy
            return {'look':'Forest','feeling':'Calm','reflection':'I would like a forest mood.','traits':''}
    provider.client=Transport()
    assert provider.journal_draft([{'role':'user','text':'Forest mood'}],'en')['traits']==''
