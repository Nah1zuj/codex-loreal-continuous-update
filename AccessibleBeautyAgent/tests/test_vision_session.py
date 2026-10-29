import base64,time
from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings
from app.vision.local_landmarks import LocalLandmarks
from test_vision_mvp import fixture
from test_phase4_flow import parsed

def test_fresh_recheck_keeps_plan_history_and_requires_owned_consent(tmp_path,monkeypatch):
    raw,geometry=fixture(left_red=40)
    monkeypatch.setattr(LocalLandmarks,'detect',lambda self,data:geometry)
    app=create_app(Settings(memory_path=tmp_path/'session.sqlite'))
    with TestClient(app) as client:
        reply=parsed(client.post('/api/chat/stream',json={'message':'我想化自然日常妆'}))
        sid=reply['session']['session_id']
        parsed(client.post('/api/chat/stream',json={'session_id':sid,'message':'开始'}))
        state=client.get('/api/session/'+sid).json();before=state['makeup_plan']['active_index']
        frame={'session_id':sid,'image':base64.b64encode(raw).decode(),'frame_id':'first','captured_at':time.time(),'explicit_consent':True,'target':'blush'}
        first=client.post('/api/vision/local',json=frame);assert first.status_code==200
        assert first.json()['observation']['assessment']['status']=='left_more_prominent'
        second=client.post('/api/vision/local',json={**frame,'frame_id':'second','captured_at':time.time(),'locale':'en'});assert second.status_code==200
        assert second.json()['message'].startswith('Your left cheek')
        assert second.json()['observation']['comparison']['comparable'] is True
        assert client.get('/api/session/'+sid).json()['makeup_plan']['active_index']==before
        assert len(client.get('/api/vision/local/'+sid).json()['observations'])==2
        assert client.post('/api/vision/local',json=frame).status_code==409
        assert client.get('/api/session/'+sid).json()['visual_state'] is None
        client.delete('/api/vision/local/'+sid)
        assert client.get('/api/vision/local/'+sid).json()['observations']==[]
        assert client.post('/api/vision/local',json={**frame,'frame_id':'denied','explicit_consent':False}).status_code==403
        with TestClient(app) as other:assert other.get('/api/vision/local/'+sid).status_code==404

def test_analyze_makeup_tool_only_reads_fresh_requested_evidence(tmp_path):
    from app.agent.tools import ToolRegistry
    from app.agent.coaching_intents import coaching_intent
    app=create_app(Settings(memory_path=tmp_path/'tools.sqlite'))
    with TestClient(app) as client:
        sid=parsed(client.post('/api/chat/stream',json={'message':'I want natural makeup','locale':'en'}))['session']['session_id']
        agent=app.state.agent;s=agent.sessions.get(sid);tools=ToolRegistry(agent)
        assert tools.execute(s,'analyze_makeup',{'target':'blush'},'check my blush')['result']['capture_required'] is True
        s.visual_state={'target':'blush','captured_at':time.time(),'simulated':False,'status':'UNCERTAIN','geometry':{'secret_landmarks':'never_forward'},'assessment':{'status':'uncertain'}}
        reply=tools.execute(s,'analyze_makeup',{'target':'blush'},'check my blush')
        assert reply['result']['available'] is True
        assert 'geometry' not in reply['result']['observation']
        assert tools.execute(s,'analyze_makeup',{'target':'lips'},'check my lips')['result']['capture_required'] is True
        assert tools.execute(s,'analyze_makeup',{'target':'blush'},'Do not check my blush')['ok'] is False
        s.visual_state['captured_at']-=31
        assert tools.execute(s,'analyze_makeup',{'target':'blush'},'check again')['result']['available'] is False
        assert tools.execute(s,'analyze_makeup',{'target':'eyes'},'check again')['error']=='invalid_arguments'
        assert coaching_intent('再看一次')=='visual'

def test_stopping_during_detection_cannot_restore_visual_state(tmp_path,monkeypatch):
    from threading import Event
    from concurrent.futures import ThreadPoolExecutor
    started,release=Event(),Event();raw,geometry=fixture()
    def detect(self,data):
        started.set();assert release.wait(5);return geometry
    monkeypatch.setattr(LocalLandmarks,'detect',detect)
    app=create_app(Settings(memory_path=tmp_path/'cancel.sqlite'))
    with TestClient(app) as client,ThreadPoolExecutor() as pool:
        sid=parsed(client.post('/api/chat/stream',json={'message':'I want natural makeup'}))['session']['session_id']
        future=pool.submit(client.post,'/api/vision/local',json={'session_id':sid,'image':base64.b64encode(raw).decode(),'frame_id':'slow','captured_at':time.time(),'explicit_consent':True})
        assert started.wait(5)
        assert client.delete('/api/vision/local/'+sid).status_code==200
        release.set();assert future.result(timeout=5).status_code==409
        assert client.get('/api/vision/local/'+sid).json()['observations']==[]
        assert client.get('/api/session/'+sid).json()['visual_state'] is None

def test_expired_numbers_are_removed_from_session_as_well_as_history(tmp_path,monkeypatch):
    from app.routes import local_vision
    raw,geometry=fixture();monkeypatch.setattr(LocalLandmarks,'detect',lambda self,data:geometry)
    app=create_app(Settings(memory_path=tmp_path/'expiry.sqlite'))
    with TestClient(app) as client:
        sid=parsed(client.post('/api/chat/stream',json={'message':'I want natural makeup'}))['session']['session_id']
        assert client.post('/api/vision/local',json={'session_id':sid,'image':base64.b64encode(raw).decode(),'frame_id':'expiry','captured_at':time.time(),'explicit_consent':True}).status_code==200
        future=time.time()+901;monkeypatch.setattr(local_vision.time,'time',lambda:future)
        assert client.get('/api/vision/local/'+sid).json()['observations']==[]
        assert client.get('/api/session/'+sid).json()['visual_state'] is None
