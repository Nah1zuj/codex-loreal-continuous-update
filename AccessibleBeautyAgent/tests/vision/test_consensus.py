import pytest

def frame(status, confidence=.9):
    return {'task': 'blush_presence', 'status': status, 'confidence': confidence, 'image_quality': 'good', 'simulated': True}

def test_unanimous():
    from app.vision.consensus import aggregate
    r = aggregate([frame('BOTH')] * 3)
    assert r['status'] == 'BOTH' and r['confidence'] == pytest.approx(.9)

def test_conflicting():
    from app.vision.consensus import aggregate
    assert aggregate([frame('BOTH'), frame('LEFT_ONLY'), frame('UNCERTAIN')])['status'] == 'UNCERTAIN'

def test_majority_reduced_confidence():
    from app.vision.consensus import aggregate
    r = aggregate([frame('BOTH'), frame('LEFT_ONLY'), frame('BOTH')])
    assert r['status'] == 'BOTH' and .6 <= r['confidence'] < .9

def test_low_confidence_votes():
    from app.vision.consensus import aggregate
    assert aggregate([frame('BOTH', .2)] * 3)['status'] == 'UNCERTAIN'

def test_gate_failure_never_evaluates():
    from app.vision.service import VisionService
    from app.config import Settings
    class RejectGate:
        def evaluate(self, image):
            return {'gate_pass': False, 'failure_reason': '光线太暗，请移到亮一点的位置。', 'face_detected': False}
    class Spy:
        def evaluate(self, *args, **kwargs):
            pytest.fail('Makeup provider must not be called')
    service = VisionService(Settings(), gate=RejectGate(), provider=Spy())
    assert service.check('blush_presence', [b'x'] * 3)['visual'] is None
