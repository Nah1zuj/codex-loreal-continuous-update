import json
from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings

def app_for(tmp_path):
    return create_app(Settings(memory_path=tmp_path/'v2.sqlite',model_provider='mock',allow_remote_ai=False,deepseek_api_key='',api_key='',compatible_api_key=''))

def events(response):
    return [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]

def test_stream_returns_explicit_demo_and_context(tmp_path):
    app=app_for(tmp_path)
    with TestClient(app) as client:
        response=client.post('/api/chat/stream',json={'message':'今天我想聊一聊','locale':'zh-CN'})
        assert response.status_code==200
        rows=events(response)
        assert rows[0]['type']=='session'
        assert any(r['type']=='delta' for r in rows)
        final=next(r for r in rows if r['type']=='final')
        assert final['reply']['mode']=='mock'
        sid=final['reply']['session']['session_id']
        assert app.state.conversation.history(sid)[0]['text']=='今天我想聊一聊'
        assert client.post('/api/chat/stream',json={'session_id':sid,'message':'开始步骤'}).status_code==200

def test_tool_registry_never_grants_consent_or_arbitrary_tools(tmp_path):
    from app.agent.tools import ToolRegistry
    app=app_for(tmp_path);s=app.state.agent.sessions.create()
    tools=ToolRegistry(app.state.agent)
    assert tools.execute(s,'shell',{'command':'anything'})['error']=='unknown_tool'
    assert tools.execute(s,'advance_step',{},user_text='聊聊天')['error']=='explicit_action_required'
    assert tools.execute(s,'search_knowledge',{'query':'自然','injected':True})['error']=='invalid_arguments'
    assert tools.execute(s,'current_step',{})['ok'] is True
    assert tools.execute(s,'create_plan',{'look_id':'clean_daily'},user_text='Tell me about rain')['error']=='explicit_action_required'

def test_remote_stream_consumes_real_chunks_without_exposing_transport_errors():
    from app.services.model_client import parse_stream_line
    assert parse_stream_line('data: '+json.dumps({'choices':[{'delta':{'content':'Hello'}}]}))['choices'][0]['delta']['content']=='Hello'
    assert parse_stream_line('data: [DONE]') is None
    assert parse_stream_line(': heartbeat') is None

def test_open_multiturn_stream_keeps_roles_and_plain_text_policy(tmp_path,monkeypatch):
    from app.agent import conversation
    seen=[]
    class Transport:
        def __init__(self,*args):pass
        async def stream_chat(self,model,messages,tools=None):
            seen.append(messages.copy())
            assert 'Return JSON with one message string' not in messages[0]['content']
            yield {'choices':[{'delta':{'content':'Let us talk about your story.'}}]}
            yield {'choices':[],'usage':{'prompt_tokens':20,'completion_tokens':10,'total_tokens':30}}
    monkeypatch.setattr(conversation,'RemoteModelClient',Transport)
    app=app_for(tmp_path);app.state.agent.settings.model_provider='deepseek'
    with TestClient(app) as c:
        rows=events(c.post('/api/chat/stream',json={'message':'Tell me a story about a forest','locale':'en'}))
        sid=rows[0]['session_id']
        c.post('/api/chat/stream',json={'message':'Make it about rain instead','session_id':sid,'locale':'en'})
        assert [m['role'] for m in seen[1]][-3:]==['user','assistant','user']
        assert seen[1][-3]['content']=='Tell me a story about a forest'
        assert app.state.conversation.metrics[-1]['usage']['total_tokens']==30

def test_usage_sums_all_tool_rounds(tmp_path,monkeypatch):
    from app.agent import conversation
    class Transport:
        def __init__(self,*args):self.round=0
        async def stream_chat(self,model,messages,tools=None):
            self.round+=1
            if self.round==1:
                yield {'choices':[{'delta':{'tool_calls':[{'index':0,'id':'test-memory','function':{'name':'get_memory','arguments':'{}'}}]}}]}
                yield {'choices':[],'usage':{'prompt_tokens':4,'completion_tokens':1,'total_tokens':5}}
            else:
                yield {'choices':[{'delta':{'content':'Preferences remain unchanged.'}}]}
                yield {'choices':[],'usage':{'prompt_tokens':7,'completion_tokens':3,'total_tokens':10}}
    monkeypatch.setattr(conversation,'RemoteModelClient',Transport)
    app=app_for(tmp_path);app.state.agent.settings.model_provider='deepseek'
    with TestClient(app) as c:
        rows=events(c.post('/api/chat/stream',json={'message':'What preferences did I confirm?','locale':'en'}))
        assert rows[-1]['type']=='final'
        assert app.state.conversation.metrics[-1]['usage']['total_tokens']==15

def test_missing_proxy_dependency_emits_error_instead_of_breaking_stream(tmp_path,monkeypatch):
    import socket
    from app.services import model_client
    def forbid_network(*args,**kwargs):raise AssertionError('Network is forbidden in this regression test')
    monkeypatch.setattr(socket.socket,'connect',forbid_network)
    app=app_for(tmp_path)
    app.state.agent.settings.model_provider='deepseek'
    app.state.agent.settings.allow_remote_ai=True
    app.state.agent.settings.deepseek_api_key='dummy-test-value'
    app.state.agent.settings.deepseek_base_url='http://127.0.0.1:9'
    def unavailable(*args,**kwargs):raise ImportError('socksio missing; dummy-test-value')
    monkeypatch.setattr(model_client.httpx,'AsyncClient',unavailable)
    with TestClient(app) as client:
        rows=events(client.post('/api/chat/stream',json={'message':'test input'}))
    assert rows[-1]['type']=='error'
    assert 'dummy-test-value' not in json.dumps(rows)
    assert app.state.conversation.metrics[-1]['outcome']=='failed'

def test_model_error_reasons_do_not_expose_provider_payloads():
    import httpx
    from app.services.model_client import ModelServiceError
    request=httpx.Request('POST','https://unused.invalid')
    for status,expected in [(401,'拒绝访问'),(403,'拒绝访问'),(429,'受限'),(503,'调用失败')]:
        response=httpx.Response(status,request=request,text='do-not-expose-provider-body')
        error=ModelServiceError(httpx.HTTPStatusError('do-not-expose-private-details',request=request,response=response))
        assert expected in error.public_message
        assert 'do-not-expose' not in str(error)
    assert '超时' in str(ModelServiceError(httpx.ReadTimeout('private-details')))
    assert '连接失败' in str(ModelServiceError(httpx.ProxyError('private-details')))

def test_deepseek_voice_requests_disable_thinking_without_changing_other_providers(monkeypatch):
    import asyncio,httpx
    from app.services import model_client
    captured=[]
    async_client=httpx.AsyncClient
    def handle(request):
        captured.append(json.loads(request.content))
        return httpx.Response(200,content='data: {"choices":[{"delta":{"content":"OK"},"finish_reason":"stop"}]}\n\ndata: [DONE]\n\n',headers={'content-type':'text/event-stream'})
    monkeypatch.setattr(model_client.httpx,'AsyncClient',lambda **kwargs:async_client(transport=httpx.MockTransport(handle),trust_env=False))
    settings=Settings(model_provider='mock',allow_remote_ai=True,deepseek_api_key='dummy',api_key='dummy',deepseek_base_url='https://unused.invalid',base_url='https://unused.invalid')
    async def check():
        for provider in ['deepseek','qwen']:
            rows=[row async for row in model_client.RemoteModelClient(settings,provider).stream_chat('test-model',[{'role':'user','content':'test input'}])]
            assert rows[0]['choices'][0]['delta']['content']=='OK'
    asyncio.run(check())
    assert captured[0]['thinking']=={'type':'disabled'}
    assert 'thinking' not in captured[1]
