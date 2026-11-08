"""Synthetic frames exercise privacy, revocation and quality, not physical accuracy."""
import base64
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import cv2
import numpy as np
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.vision.local_landmarks import LocalLandmarks
from test_vision_mvp import fixture


def grant(client, sid, scope='camera'):
    response = client.post('/api/vision/local/permits', json={'session_id': sid, 'scope': scope})
    assert response.status_code == 200, response.text
    return response.json()


def frame(sid, raw, permit, frame_id, **changes):
    return {
        'session_id': sid, 'image': base64.b64encode(raw).decode(), 'captured_at': time.time(),
        'permit_id': permit['permit_id'], 'baseline_version': permit['baseline_version'],
        'frame_id': frame_id, 'explicit_consent': True, **changes,
    }


def test_distinct_permits_no_automatic_baseline_and_scoped_revoke(tmp_path, monkeypatch):
    raw, geometry = fixture(left_red=25)
    monkeypatch.setattr(LocalLandmarks, 'detect', lambda self, data: geometry)
    with TestClient(create_app(Settings(memory_path=tmp_path/'scopes.sqlite'))) as client:
        sid = client.post('/api/session', json={}).json()['session_id']
        denied = client.post('/api/vision/local/permits', json={'session_id': sid, 'scope': 'adaptive'})
        assert denied.status_code == 403
        camera = grant(client, sid)
        adaptive = grant(client, sid, 'adaptive')
        assert client.post('/api/vision/local', json=frame(sid, raw, camera, 'scope-mismatch', adaptive=True)).status_code == 403
        first = client.post('/api/vision/local', json=frame(sid, raw, camera, 'first')).json()['observation']
        assert first['comparison'] is None
        auto = frame(sid, raw, adaptive, 'auto', adaptive=True, compare_baseline=True)
        assert client.post('/api/vision/local', json=auto).json()['observation']['comparison'] is None
        assert client.post('/api/vision/local', json={**auto, 'baseline_consent': True}).status_code == 409
        assert client.request('DELETE', '/api/vision/local/'+sid, json={'permit_id': adaptive['permit_id']}).status_code == 200
        assert client.get('/api/vision/local/'+sid).json()['observations'] == []
        assert client.post('/api/vision/local', json={**auto, 'frame_id': 'late-auto'}).status_code == 403
        assert client.post('/api/vision/local', json=frame(sid, raw, camera, 'manual-still-valid')).status_code == 200


def test_baseline_clearing_cancels_inflight_and_rejects_late_baseline_requests(tmp_path, monkeypatch):
    raw, geometry = fixture(left_red=25)
    started, release = Event(), Event()

    def detect(self, data):
        started.set()
        assert release.wait(5)
        return geometry

    monkeypatch.setattr(LocalLandmarks, 'detect', detect)
    with TestClient(create_app(Settings(memory_path=tmp_path/'baseline.sqlite'))) as client, ThreadPoolExecutor() as pool:
        sid = client.post('/api/session', json={}).json()['session_id']
        permit = grant(client, sid)
        body = frame(sid, raw, permit, 'slow-baseline', baseline_consent=True)
        pending = pool.submit(client.post, '/api/vision/local', json=body)
        try:
            assert started.wait(5)
            cleared = client.request('DELETE', '/api/vision/local/'+sid,
                                     json={'baseline': True, 'permit_id': permit['permit_id']})
            assert cleared.status_code == 200
            assert cleared.json()['baseline_version'] > permit['baseline_version']
        finally:
            release.set()
        assert pending.result(timeout=5).status_code == 409
        assert client.post('/api/vision/local', json={**body, 'frame_id': 'old-baseline'}).status_code == 409
        assert client.get('/api/vision/local/'+sid).json() == {
            'observations': [], 'baseline_available': False, 'images_saved': False,
        }


def test_restore_revokes_all_permits_and_clears_temporary_values(tmp_path, monkeypatch):
    raw, geometry = fixture()
    monkeypatch.setattr(LocalLandmarks, 'detect', lambda self, data: geometry)
    with TestClient(create_app(Settings(memory_path=tmp_path/'restore.sqlite'))) as client:
        sid = client.post('/api/session', json={}).json()['session_id']
        permit = grant(client, sid)
        assert client.post('/api/vision/local', json=frame(sid, raw, permit, 'baseline', baseline_consent=True)).status_code == 200
        assert client.get('/api/vision/local/'+sid).json()['baseline_available']
        assert client.post('/api/session/'+sid+'/restore').status_code == 200
        assert client.get('/api/vision/local/'+sid).json()['observations'] == []
        assert client.post('/api/vision/local', json=frame(sid, raw, permit, 'after-restore')).status_code == 403


def test_local_route_never_calls_remote_followup_or_echoes_frame(tmp_path, monkeypatch):
    from app.agent import conversation
    from app.services.model_client import RemoteModelClient
    raw, geometry = fixture()
    monkeypatch.setattr(LocalLandmarks, 'detect', lambda self, data: geometry)

    def remote(*args, **kwargs):
        raise AssertionError('A local-only check must not call a remote model')

    monkeypatch.setattr(RemoteModelClient, 'chat_json', remote)
    settings = Settings(memory_path=tmp_path/'offline.sqlite', model_provider='deepseek', allow_remote_ai=True)
    with TestClient(create_app(settings)) as client:
        sid = client.post('/api/session', json={}).json()['session_id']
        permit = grant(client, sid)
        body = frame(sid, raw, permit, 'local-only')
        response = client.post('/api/vision/local', json=body)
        assert response.status_code == 200
        assert response.json()['observation']['source'] == 'local_mediapipe'
        assert body['image'] not in response.text
        assert response.json()['message'] and response.json()['session']['last_response'] == ''
        assert client.get('/api/session/'+sid).json()['last_response'] == ''
        invalid = client.post('/api/vision/local', json={**body, 'target': 'invalid', 'extra_frame': body['image']})
        assert invalid.status_code == 422
        assert body['image'] not in invalid.text

        requests = []

        class RemoteTextFixture:
            def __init__(self, *_):
                pass

            async def stream_chat(self, model, messages, tools):
                requests.append((messages[0]['content'], tools))
                yield {'choices': [{'delta': {'content': 'Tell me more about your day.'}}]}

        monkeypatch.setattr(conversation, 'RemoteModelClient', RemoteTextFixture)
        reply = client.post('/api/chat/stream', json={'session_id': sid, 'message': 'Tell me a story', 'locale': 'en'})
        assert reply.status_code == 200 and requests
        policy, tools = requests[0]
        assert '"scope": "local_only"' in policy
        assert response.json()['observation']['observation_id'] not in policy
        assert 'mediapipe_masked_lab' not in policy and body['image'] not in policy
        assert all('visual' not in tool['function']['name'] and tool['function']['name'] != 'analyze_makeup' for tool in tools)


def test_synthetic_quality_and_baseline_comparability(tmp_path, monkeypatch):
    raw, geometry = fixture(left_red=25)
    detected = geometry.copy()
    monkeypatch.setattr(LocalLandmarks, 'detect', lambda self, data: detected)
    with TestClient(create_app(Settings(memory_path=tmp_path/'quality.sqlite'))) as client:
        sid = client.post('/api/session', json={}).json()['session_id']
        permit = grant(client, sid)
        captured = client.post('/api/vision/local', json=frame(sid, raw, permit, 'baseline', baseline_consent=True))
        assert captured.json()['observation']['baseline_saved']
        gray = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        for name, pixels in [
            ('dim', np.clip(gray.astype(float)-25, 0, 255).astype(np.uint8)),
            ('blur', np.full_like(gray, 120)),
        ]:
            sample = cv2.imencode('.png', pixels)[1].tobytes()
            r = client.post('/api/vision/local', json=frame(sid, sample, permit, name, compare_baseline=True))
            result = r.json()['observation']
            assert result['comparison'] is None or result['comparison']['comparable'] is False
            if name == 'blur':
                assert 'blur' in result['quality']['warnings']
        for count, expected in [(0,'no_face'), (2,'multiple_faces')]:
            detected['face_count'] = count
            r = client.post('/api/vision/local', json=frame(sid, raw, permit, expected, compare_baseline=True))
            assert expected in r.json()['observation']['quality']['warnings']
        detected['face_count'] = 1
        white_patch = gray.copy()
        white_patch[100:156, 60:200] = 255
        clipped = cv2.imencode('.png', white_patch)[1].tobytes()
        result = client.post('/api/vision/local', json=frame(sid, clipped, permit, 'clipped')).json()['observation']
        assert result['quality']['usable'] is False
        assert 'region_occluded_or_clipped' in result['quality']['warnings']
