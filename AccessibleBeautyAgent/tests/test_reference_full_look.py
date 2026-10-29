import json
from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings

def test_full_look_can_follow_the_active_coaching_plan_without_a_legacy_look(tmp_path):
    with TestClient(create_app(Settings(memory_path=tmp_path/'reference.sqlite'))) as client:
        stream=client.post('/api/chat/stream',json={'message':'我想要自然的日常妆，十五分钟。'})
        reply=[json.loads(line[6:]) for line in stream.text.splitlines() if line.startswith('data: ')][-1]['reply']
        s=reply['session']
        assert s['makeup_plan'] and not s['selected_look']
        look=client.post('/api/full-look/plan',json={'session_id':s['session_id']})
        assert look.status_code==200
        result=look.json()
        assert result['session']['makeup_plan']==s['makeup_plan']
        assert result['session']['selected_look'] is None
        assert result['plan']['sections']['makeup']['suggestions'][0]['id']=='coaching_makeup'
        assert result['plan']['sections']['makeup']['look_id'] is None
