import asyncio
import json

import httpx
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.schemas.models import ChatRequest


def test_health_reports_configuration_without_creating_personal_identity(tmp_path):
    settings = Settings(memory_path=tmp_path / 'health.sqlite', model_provider='openai_compatible',
                        allow_remote_ai=True, compatible_api_key='test-private-key',
                        compatible_model='fake-model', compatible_base_url='')
    with TestClient(create_app(settings)) as client:
        response = client.get('/api/health')
        assert response.status_code == 200
        assert 'set-cookie' not in response.headers
        assert 'test-private-key' not in response.text
        assert response.json()['readiness']['sqlite_ready'] is True
        assert response.json()['readiness']['remote_text_configured'] is False
        assert response.json()['readiness']['remote_text_verified'] is False
        assert response.json()['readiness']['vision_inference_verified'] is False
        for endpoint in ('ftp://unused.invalid', 'https:///no-host', 'https://[malformed'):
            settings.compatible_base_url = endpoint
            readiness = client.get('/api/health').json()['readiness']
            assert readiness['remote_text_configured'] is False
            assert readiness['remote_text_verified'] is False
        with client.app.state.agent.memory.connect() as db:
            assert db.execute('SELECT COUNT(*) FROM browser_identities').fetchone() == (0,)


def test_remote_text_proof_requires_a_finished_remote_turn_for_the_active_configuration(tmp_path, monkeypatch):
    from app.services import model_client

    settings = Settings(memory_path=tmp_path / 'remote-health.sqlite', model_provider='openai_compatible',
                        allow_remote_ai=True, compatible_api_key='fixture-private-key',
                        compatible_model='test-model', compatible_base_url='https://unused.invalid/v1')
    app = create_app(settings)
    responses = iter([
        httpx.Response(200, text='data: {"choices":[{"delta":{"content":"Provider narration"},"finish_reason":"stop"}]}\n\n'),
        httpx.Response(200, text='data: {"choices":[{"delta":{"content":"Interrupted text"}}]}\n\n'),
        httpx.Response(200, text='data: {"choices":[{"delta":{"content":"  "},"finish_reason":"stop"}]}\n\n'),
        httpx.Response(503, text='fixture-private-provider-error'),
        httpx.Response(200, text='data: {"choices":[{"delta":{"content":"Completed text"},"finish_reason":"stop"}]}\n\ndata: [DONE]\n\n'),
    ])
    async_client = httpx.AsyncClient

    def respond(request):
        assert request.url.path == '/v1/chat/completions'
        assert json.loads(request.content)['model'] == 'test-model'
        return next(responses)

    monkeypatch.setattr(model_client.httpx, 'AsyncClient',
                        lambda **kwargs: async_client(transport=httpx.MockTransport(respond), trust_env=False))

    with TestClient(app) as client:
        def ready():
            result = client.get('/api/health')
            assert 'fixture-private-key' not in result.text
            return result.json()['readiness']

        def turn(message):
            response = client.post('/api/chat/stream', json={'message': message, 'locale': 'en'})
            assert 'fixture-private-provider-error' not in response.text
            return [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')][-1]

        assert ready()['remote_text_configured'] is True
        assert ready()['remote_text_verified'] is False
        assert turn('stop camera')['diagnostics'] == {'provider': 'local', 'remote_response_verified': False}
        canonical = turn('I want natural makeup')
        assert canonical['diagnostics'] == {'provider': 'local', 'remote_response_verified': False}
        assert canonical['reply']['message'] != 'Provider narration'
        assert turn('Tell me a story')['diagnostics'] == {'provider': 'openai_compatible', 'remote_response_verified': False}
        assert ready()['remote_text_verified'] is False
        assert turn('Tell me a story')['type'] == 'error'  # Empty answer despite a terminal marker.
        assert turn('Tell me a story')['type'] == 'error'  # Provider failure.
        assert ready()['remote_text_verified'] is False

        completed = turn('Tell me a story')
        assert completed['type'] == 'final'
        assert completed['diagnostics'] == {'provider': 'openai_compatible', 'remote_response_verified': True}
        metrics = client.get('/api/diagnostics').json()['turns']
        assert [turn['remote_response_verified'] for turn in metrics] == [False, False, False, False, False, True]
        assert metrics[-1]['provider'] == 'openai_compatible'
        assert metrics[-1]['usage'] is None
        assert ready()['remote_text_verified'] is True

        for field, changed in [('compatible_model', 'another-model'), ('compatible_base_url', 'https://other.invalid/v1'),
                               ('compatible_api_key', 'different-test-key'), ('allow_remote_ai', False),
                               ('model_provider', 'mock')]:
            previous = getattr(settings, field)
            setattr(settings, field, changed)
            assert ready()['remote_text_verified'] is False
            setattr(settings, field, previous)

    with TestClient(create_app(settings)) as restarted:
        assert restarted.get('/api/health').json()['readiness']['remote_text_verified'] is False


def test_cancelled_remote_text_turn_never_records_proof(tmp_path, monkeypatch):
    from app.agent import conversation

    class Transport:
        def __init__(self, *_):
            pass

        async def stream_chat(self, *_):
            yield {'choices': [{'delta': {'content': 'Test text'}, 'finish_reason': 'stop'}]}

    class Request:
        disconnected = False

        async def is_disconnected(self):
            return self.disconnected

    settings = Settings(memory_path=tmp_path / 'cancelled-health.sqlite', model_provider='deepseek',
                        allow_remote_ai=True, deepseek_api_key='fixture-key')
    service = create_app(settings).state.conversation
    monkeypatch.setattr(conversation, 'RemoteModelClient', Transport)

    async def cancel():
        request = Request()
        events = service.stream(ChatRequest(message='Tell me a story'), request)
        assert (await anext(events))['type'] == 'session'
        assert (await anext(events))['type'] == 'delta'
        request.disconnected = True
        assert [event async for event in events] == []

    asyncio.run(cancel())
    assert service.remote_text_readiness() == (True, False)
    assert service.metrics[-1]['outcome'] == 'cancelled'
    assert service.metrics[-1]['remote_response_verified'] is False
