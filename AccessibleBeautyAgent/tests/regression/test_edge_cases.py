import io
import base64
import pytest
from PIL import Image
from test_acceptance import client,chat

def test_blank_image_rejected_by_real_gate(client):
    r=chat(client,'dinner')
    sid=r['session']['session_id']
    chat(client,'check this',sid)
    chat(client,'',sid,action='camera_consent',consent=True)
    buffer=io.BytesIO()
    Image.new('RGB',(320,320),(12,12,12)).save(buffer,format='JPEG')
    encoded=base64.b64encode(buffer.getvalue()).decode()
    agent=client.app.state.agent
    original=agent.vision.provider
    class Spy:
        def evaluate(self,*args):pytest.fail('Failed gate must block provider')
    agent.vision.provider=Spy()
    try:
        response=client.post('/api/vision/check',json={'session_id':sid,'task':'blush_presence','images':[encoded]*3})
        assert response.status_code==200,response.text
        assert response.json()['visual'] is None
        assert response.json()['gate']['gate_pass'] is False
        assert response.json()['session']['camera_consent'] is False
    finally:agent.vision.provider=original

def test_demo_cannot_bypass_gate_in_normal_mode(client):
    r=chat(client,'dinner');sid=r['session']['session_id']
    chat(client,'check this',sid);chat(client,'',sid,action='camera_consent',consent=True)
    client.app.state.settings.developer_mode=False
    assert client.post('/api/vision/check',json={'session_id':sid,'demo':True,'images':[]}).status_code==403

def test_free_text_cannot_grant_camera_consent(client):
    r=chat(client,'dinner');sid=r['session']['session_id']
    chat(client,'check this',sid)
    r=chat(client,'同意 开相机',sid)
    assert not r['session']['camera_consent']

def test_incomplete_frames_rejected(client):
    r=chat(client,'dinner');sid=r['session']['session_id']
    chat(client,'check this',sid);chat(client,'',sid,action='camera_consent',consent=True)
    r=client.post('/api/vision/check',json={'session_id':sid,'images':[]})
    assert r.status_code==409
    assert not client.get('/api/session/'+sid).json()['camera_consent']

def test_reference_draft_is_unverified():
    from app.vision.reference import MockVisionReferenceAnalyzer
    r=MockVisionReferenceAnalyzer().analyze(b'')
    assert r['human_verified'] is False and r['verified'] is False
    assert r['blush']['visible'] is None

def test_invalid_visual_status_rejected():
    from app.schemas.models import VisualResult
    with pytest.raises(ValueError):VisualResult(task='lip_presence',status='BOTH',confidence=.9)

def test_repeat_does_not_advance(client):
    r=chat(client,'daily');sid=r['session']['session_id']
    chat(client,'开始步骤',sid)
    r=chat(client,'repeat',sid)
    assert r['session']['routine_step']==0
    assert r['message'].startswith('重复')

def test_empty_intent_clarifies(client):
    r=chat(client,'我想试一试')
    assert r['session']['stage']=='CLARIFY'
    assert r['session']['selected_look'] is None

def test_low_demo_confidence_no_observation(client):
    r=chat(client,'dinner');sid=r['session']['session_id']
    chat(client,'check this',sid);chat(client,'',sid,action='camera_consent',consent=True)
    r=client.post('/api/vision/check',json={'session_id':sid,'demo':True,'mock_status':'UNCERTAIN','images':[]}).json()
    assert r['visual']['status']=='UNCERTAIN'
    assert '不想随便猜' in r['message']

def test_lip_task(client):
    r=chat(client,'daily');sid=r['session']['session_id']
    chat(client,'check this',sid);chat(client,'',sid,action='camera_consent',consent=True)
    r=client.post('/api/vision/check',json={'session_id':sid,'task':'lip_presence','demo':True,'mock_status':'APPLIED','images':[]})
    assert r.status_code==200,r.text
    assert r.json()['visual']['status']=='APPLIED'

def test_remote_error_does_not_fake_result(client):
    r=chat(client,'dinner');sid=r['session']['session_id']
    chat(client,'check this',sid);chat(client,'',sid,action='camera_consent',consent=True)
    class Broken:
        def check(self,*args,**kwargs):raise RuntimeError('Remote provider unavailable')
    client.app.state.agent.vision=Broken()
    r=client.post('/api/vision/check',json={'session_id':sid,'demo':True,'images':[]})
    assert r.status_code==503
    state=client.get('/api/session/'+sid).json()
    assert state['visual_state'] is None
    assert state['camera_consent'] is False

def test_rag_parent_hierarchy(client):
    docs=client.app.state.agent.retriever.documents
    ids={d['document_id'] for d in docs}
    assert all(not d['metadata']['parent_id'] or d['metadata']['parent_id'] in ids for d in docs)
    assert {d['document_type'] for d in docs}=={'LOOK','ROUTINE','PRODUCT','REFERENCE_CASE','ACCESSIBILITY_GUIDANCE'}
