import cv2,numpy as np
import pytest
from app.vision.local_landmarks import LocalLandmarks,region_measurements,MODEL

def test_real_local_model_executes_on_blank_pixels_without_inventing_face():
    if not MODEL.exists():pytest.skip('Official local model not installed')
    detector=LocalLandmarks()
    raw=cv2.imencode('.png',np.zeros((160,160,3),np.uint8))[1].tobytes()
    result=detector.detect(raw)
    assert detector.status=='ready'
    assert result['face_count']==0 and result['points']==[]
    detector.close()

def test_invalid_landmarks_reject_and_subject_left_uses_unmirrored_pixels():
    raw=cv2.imencode('.png',np.full((160,160,3),120,np.uint8))[1].tobytes()
    with pytest.raises(ValueError):region_measurements(raw,[(float('nan'),0,0)]*478)
    points=[(.5,.5,0)]*478;points[50]=(.3,.5,0);points[280]=(.7,.5,0)
    regions,measurement,count=region_measurements(raw,points)
    assert count==478 and regions['left_cheek']['area']>0
    assert measurement['regions']==regions
