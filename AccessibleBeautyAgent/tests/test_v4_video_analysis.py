import base64
import io
import pytest
from PIL import Image
from test_acceptance import client, chat

def sample():
    out=io.BytesIO();Image.new('RGB',(64,64),(120,120,120)).save(out,format='PNG')
    return 'data:image/png;base64,'+base64.b64encode(out.getvalue()).decode()

def body(client, consent=True):
    sid=chat(client,'dinner')['session']['session_id']
    chat(client,'check this',sid)
    if consent: chat(client,'',sid,action='camera_consent',consent=True)
    return dict(session_id=sid,task='blush_presence',images=[sample()],capture_kind='video_sample',remote_frame_consent=False)

def test_video_requires_camera_consent(client):
    assert client.post('/api/vision/check',json=body(client,False)).status_code==403

def test_single_sample_is_accepted_with_existing_local_gate(client):
    response=client.post('/api/vision/check',json=body(client))
    assert response.status_code==200,response.text
    assert response.json()['visual'] is None  # synthetic non-face stays uncertain

@pytest.mark.parametrize('change',[{'images':[]},{'images':[sample(),sample()]},{'video_blob':'secret'},{'video_frames':[]},{'remote_frame_consent':'true'},{'task':'composition'}])
def test_video_shape_and_task_restricted(client,change):
    payload=body(client);payload.update(change)
    assert client.post('/api/vision/check',json=payload).status_code==422

def test_video_remote_consent_is_per_request(client):
    payload=body(client)
    settings=client.app.state.agent.settings
    settings.vision_provider='qwen';settings.allow_remote_ai=True
    assert client.post('/api/vision/check',json=payload).status_code==403
    payload.pop('remote_frame_consent')
    assert client.post('/api/vision/check',json=payload).status_code==403

def test_photo_three_frame_contract_preserved(client):
    payload=body(client);payload.pop('capture_kind');payload.pop('remote_frame_consent');payload['images']=[sample()]*3
    assert client.post('/api/vision/check',json=payload).status_code==200
def test_video_success_retains_active_camera_consent_until_explicit_revoke(client):
    payload=body(client)
    agent=client.app.state.agent
    agent.vision.gate.evaluate=lambda _: {'gate_pass':True}
    for _ in range(2):
        response=client.post('/api/vision/check',json=payload)
        assert response.status_code==200,response.text
        assert response.json()['session']['camera_consent'] is True
        assert response.json()['session']['last_tool_call']['arguments']['frame_count']==1
    chat(client,'',payload['session_id'],action='camera_consent',consent=False)
    assert client.post('/api/vision/check',json=payload).status_code==403

def test_single_sample_low_confidence_stays_uncertain(client):
    payload=body(client);agent=client.app.state.agent
    agent.vision.gate.evaluate=lambda _: {'gate_pass':True}
    agent.vision.provider.evaluate=lambda *args: dict(task='blush_presence',status='BOTH',confidence=.2,image_quality='good')
    response=client.post('/api/vision/check',json=payload)
    assert response.status_code==200,response.text
    assert response.json()['visual']['status']=='UNCERTAIN'
    assert len(response.json()['visual']['frame_results'])==1
    assert 'agreement' not in response.json()['visual']

def test_video_sample_cannot_enter_three_frame_demo_consensus(client):
    payload=body(client);payload['demo']=True
    assert client.post('/api/vision/check',json=payload).status_code==422
