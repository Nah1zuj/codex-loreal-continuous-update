import cv2,numpy as np
import pytest
from app.vision.local_regions import LocalRegionAnalyzer

@pytest.fixture(autouse=True)
def explicit_proxy_fixture(monkeypatch):
    # These tests cover the historical proxy with synthetic geometry, not a real face.
    from app.vision.local_landmarks import LocalLandmarks
    monkeypatch.setattr(LocalLandmarks,'detect',lambda self,raw:None)

def image(red=120):
    pixels=np.full((160,160,3),(110,120,red),dtype=np.uint8)
    return cv2.imencode('.png',pixels)[1].tobytes()
class Gate:
    def evaluate(self,data):return {'gate_pass':True,'face_box':[30,20,100,120],'method':'synthetic_geometry_fixture'}

def test_local_signals_are_not_calibrated_makeup_decisions():
    analyzer=LocalRegionAnalyzer(Gate())
    result=analyzer.analyze(image(),None)
    assert result['status']=='UNCERTAIN'
    assert result['confidence'] is None and result['calibrated'] is False
    assert result['regions']['left_cheek']['area']>0
    compared=analyzer.analyze(image(130),result['measurement'])
    assert compared['comparison']['comparable'] is True
    assert compared['status']=='UNCERTAIN'

def test_bad_gate_produces_no_face_observation():
    class NoFace:
        def evaluate(self,data):return {'gate_pass':False,'failure_reason':'No face'}
    result=LocalRegionAnalyzer(NoFace()).analyze(image(),None)
    assert result['regions']=={} and result['message']=='No face'

def test_left_right_are_the_users_sides_not_mirrored_preview():
    pixels=np.full((160,160,3),(110,120,120),dtype=np.uint8)
    pixels[78:102,95:116]=(110,120,170)
    raw=cv2.imencode('.png',pixels)[1].tobytes()
    result=LocalRegionAnalyzer(Gate()).analyze(raw,None)
    assert result['regions']['left_cheek']['redness']>result['regions']['right_cheek']['redness']
