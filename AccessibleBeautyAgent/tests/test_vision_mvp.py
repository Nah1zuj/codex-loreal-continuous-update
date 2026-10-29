"""Synthetic pixels/geometry exercise rules, NOT real-person accuracy."""
import cv2
import numpy as np
import pytest
from app.vision.makeup_observation import observe_makeup

def fixture(left_red=0, dark=False, asymmetry=False):
    rng=np.random.default_rng(4)
    pixels=np.clip(145+rng.normal(0,10,(240,240,3)),0,255).astype(np.uint8)
    points=np.zeros((478,3));points[:,:2]=(.5,.5)
    points[10,:2]=(.5,.1);points[152,:2]=(.5,.9)
    points[234,:2]=(.15,.5);points[454,:2]=(.85,.5)
    points[33,:2]=(.3,.35);points[263,:2]=(.7,.35)
    points[1,:2]=(.5,.47);points[50,:2]=(.3,.52);points[280,:2]=(.7,.52)
    points[13,:2]=(.5,.70);points[14,:2]=(.5,.73)
    points[61,:2]=(.4,.71);points[291,:2]=(.6,.71)
    pixels[105:145,150:185,2]=np.clip(pixels[105:145,150:185,2].astype(int)+left_red,0,255)
    if dark:pixels//=8
    if asymmetry:pixels[:,:120]//=3
    return cv2.imencode('.png',pixels)[1].tobytes(),{'face_count':1,'points':points.tolist()}

def test_anatomical_left_has_more_color_without_claiming_blush_accuracy():
    result=observe_makeup(*fixture(left_red=45),target='blush')
    assert result['assessment']['status']=='left_more_prominent'
    assert result['confidence'] is None and result['calibrated'] is False
    assert result['assessment']['scope']=='relative_cheek_color_not_makeup_coverage'
    assert result['regions']['left_cheek']['redness']>result['regions']['right_cheek']['redness']
    assert 'landmarks' not in result['geometry']  # no raw biometric geometry in agent context

def test_dark_and_asymmetric_lighting_are_uncertain():
    for args in ({'dark':True},{'asymmetry':True}):
        result=observe_makeup(*fixture(**args),target='blush')
        assert result['assessment']['status']=='uncertain'
        assert result['measurement'] is None
        assert result['quality_warnings']

def test_recheck_compares_features_not_arbitrary_improvement():
    before=observe_makeup(*fixture(left_red=45),target='blush')
    after=observe_makeup(*fixture(left_red=25),target='blush',previous=before['measurement'])
    assert after['comparison']['comparable'] is True
    assert after['comparison']['imbalance_delta']<0
    assert after['comparison']['claim']=='color_difference_change_not_makeup_improvement'
    changed={**before['measurement'],'lighting':5}
    assert observe_makeup(*fixture(),target='blush',previous=changed)['comparison']['comparable'] is False

def test_no_multiple_invalid_face_or_lips_never_gets_coverage_success():
    raw,detected=fixture()
    for count in (0,2):
        result=observe_makeup(raw,{'face_count':count,'points':[]})
        assert result['assessment']['status']=='uncertain'
    detected['points'][1][0]=float('nan')
    assert observe_makeup(raw,detected)['assessment']['status']=='uncertain'
    lip=observe_makeup(*fixture(),target='lips')
    assert lip['assessment']['status']=='uncertain'
    assert lip['regions']['lip_proxy']['area']>0

def test_pose_and_blur_rejected():
    raw,detected=fixture();detected['points'][1][0]=.68
    assert 'pose' in observe_makeup(raw,detected)['quality_warnings']
    raw,detected=fixture();pixels=cv2.imdecode(np.frombuffer(raw,np.uint8),1)
    raw=cv2.imencode('.png',cv2.GaussianBlur(pixels,(31,31),12))[1].tobytes()
    assert 'blur' in observe_makeup(raw,detected)['quality_warnings']

def test_roll_uses_pixel_aspect_ratio():
    raw,detected=fixture();pixels=cv2.imdecode(np.frombuffer(raw,np.uint8),1)
    raw=cv2.imencode('.png',cv2.resize(pixels,(480,240)))[1].tobytes()
    detected['points'][263][1]=.45
    result=observe_makeup(raw,detected)
    assert result['geometry']['head_pose']['roll']==pytest.approx(7.13,abs=.01)
