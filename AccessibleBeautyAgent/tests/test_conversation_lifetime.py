from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_idle_session_stream_locks_are_released_while_recent_context_remains(tmp_path):
    app = create_app(Settings(memory_path=tmp_path / 'locks.sqlite'))
    with TestClient(app) as client:
        for index in range(20):
            reply = client.post('/api/chat/stream', json={'message': f'测试回合 {index+1}'})
            assert reply.status_code == 200
            assert '"type": "final"' in reply.text
        service = app.state.conversation
        assert len(service.turns) == 20
        assert not service.locks
