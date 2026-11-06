from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


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
        with client.app.state.agent.memory.connect() as db:
            assert db.execute('SELECT COUNT(*) FROM browser_identities').fetchone() == (0,)
