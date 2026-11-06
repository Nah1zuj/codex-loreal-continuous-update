from app.config import Settings

def test_registry_loads_six_versioned_runtime_policies():
 from app.policies.registry import PolicyRegistry
 r=PolicyRegistry()
 assert PolicyRegistry(version='v4').version=='v4'
 assert len(r.manifest())==6
 assert all(x['version']=='v5' and len(x['sha256'])==64 for x in r.manifest())
 assert '用户' in r.system('accessibility_policy')

def test_language_provider_uses_runtime_policy_not_unused_markdown():
 from app.agent.providers import DeepSeekLanguageProvider
 p=DeepSeekLanguageProvider(Settings(model_provider='deepseek',allow_remote_ai=False))
 seen=[]
 def fake(model,system,content):seen.append(system);return {'scene':'dinner','desired_impression':[],'avoid':[]}
 p.client.chat_json=fake
 assert p.understand('dinner').scene=='dinner'
 assert 'accessibility_policy' in seen[0] and 'full_look_planner_policy' in seen[0]

def test_garment_unclear_percentage_returns_unknown_without_guess():
 from app.reading.service import ReadingService
 s=ReadingService(Settings(reading_provider='mock'))
 real=s.read(b'fake',label_kind='garment')
 assert real['status']=='UNCERTAIN' and real['composition'] is None
 demo=s.read(b'',demo=True,label_kind='garment')
 assert demo['simulated'] and demo['composition'] and '虚构' in demo['summary']

def test_remote_unclear_characters_drop_high_confidence_composition(monkeypatch):
 from app.reading.service import ReadingService
 from app.services.model_client import RemoteModelClient
 monkeypatch.setattr(RemoteModelClient,'chat_json',lambda *args:{'summary':'看不清','composition':'100% cotton','confidence':.99,'uncertain_characters':['百分比不清楚']})
 s=ReadingService(Settings(reading_provider='deepseek',allow_remote_ai=True,deepseek_vision_model='stub'))
 r=s.read(b'fake',label_kind='garment')
 assert r['status']=='UNCERTAIN' and r['composition'] is None
