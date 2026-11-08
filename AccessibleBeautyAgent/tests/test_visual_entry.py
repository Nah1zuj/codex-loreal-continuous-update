from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings
from test_local_vision_permits import grant
import cv2,numpy as np,time,base64

def test_visual_session_starts_without_chat_or_media_grant(tmp_path):
    app=create_app(Settings(memory_path=tmp_path/'entry.sqlite'))
    with TestClient(app) as owner, TestClient(app) as other:
        r=owner.post('/api/session',json={'locale':'zh-CN','experience_mode':'visual'})
        assert r.status_code==200
        s=r.json();assert s['session_id'] and s['camera_consent'] is False and not s['makeup_plan']
        assert other.get('/api/session/'+s['session_id']).status_code==404

def test_uploaded_photo_is_local_consent_gated_and_has_unknown_orientation(tmp_path):
    with TestClient(create_app(Settings(memory_path=tmp_path/'photo.sqlite'))) as client:
        s=client.post('/api/session',json={}).json()
        _,image=cv2.imencode('.jpg',np.full((256,256,3),180,np.uint8))
        body={'session_id':s['session_id'],'capture_kind':'photo','image':base64.b64encode(image).decode(),'frame_id':'photo-1','captured_at':time.time()}
        assert client.post('/api/vision/local',json=body).status_code==403
        body['permit_id']=grant(client,s['session_id'],'photo')['permit_id']
        response=client.post('/api/vision/local',json={**body,'frame_id':'photo-2','explicit_consent':True})
        assert response.status_code==200
        assert response.json()['frame_saved'] is False
        observation=response.json()['observation']
        assert observation['capture_kind']=='photo' and observation['orientation']=='unknown'
        assert observation['status']=='UNCERTAIN'
        assert client.post('/api/vision/local',json={**body,'frame_id':'photo-replay','explicit_consent':True}).status_code==403

def test_photo_never_reuses_or_claims_physical_sides_from_a_camera_baseline(tmp_path,monkeypatch):
    # Synthetic analyzer fixture exercises orientation policy, not face accuracy.
    from app.vision.local_regions import LocalRegionAnalyzer
    monkeypatch.setattr(LocalRegionAnalyzer,'analyze',lambda *args:{'measurement':{'regions':{}},'status':'HEURISTIC_OBSERVATION','method':'synthetic','source':'synthetic_fixture','regions':{'left_cheek':{'redness':1},'right_cheek':{'redness':2}},'comparison':{'comparable':True},'gate':{'gate_pass':True},'message':'Forbidden physical-side advice','assessment':{'status':'observed'}})
    with TestClient(create_app(Settings(memory_path=tmp_path/'orientation.sqlite'))) as client:
        s=client.post('/api/session',json={}).json()
        _,image=cv2.imencode('.jpg',np.full((256,256,3),180,np.uint8))
        body={'session_id':s['session_id'],'capture_kind':'photo','image':base64.b64encode(image).decode(),'frame_id':'photo-policy','captured_at':time.time(),'explicit_consent':True}
        body['permit_id']=grant(client,s['session_id'],'photo')['permit_id']
        r=client.post('/api/vision/local',json=body).json()
        assert r['observation']['comparison'] is None and r['observation']['assessment']['status']=='uncertain'
        assert 'image_right_cheek' in r['observation']['regions'] and 'left_cheek' not in r['observation']['regions']
        assert 'Forbidden' not in r['message']
        assert client.post('/api/vision/local',json={**body,'frame_id':'bad-baseline','baseline_consent':True}).status_code==409
