import pytest
from fastapi.testclient import TestClient
from app.config import Settings,ROOT
from app.main import create_app

@pytest.fixture
def client(tmp_path):
 settings=Settings(model_provider='mock',vision_provider='mock',reading_provider='mock',reference_provider='mock',embedding_provider='mock',reranker_provider='mock',allow_remote_ai=False,memory_path=tmp_path/'memory.sqlite',knowledge_dir=ROOT/'data/demo/knowledge')
 with TestClient(create_app(settings)) as c:yield c

def cafe(client):
 r=client.post('/api/chat',json={'message':'我今天去偏正式又放松的咖啡馆见朋友，想自然一点','experience_mode':'voice'})
 assert r.status_code==200
 return r.json()

def test_cafe_plan_is_six_domains_same_session(client):
 r=cafe(client);s=r['session'];p=s['todays_look']
 assert s['scene']=='cafe_meeting' and s['selected_look']=='soft_formal'
 assert p['session_id']==s['session_id'] and p['review_status']=='DEMO_CURATED'
 assert set(p['sections'])=={'skincare','makeup','hair','outfit','accessories','fragrance'}
 assert p['sections']['makeup']['routine_id']=='soft_formal_routine'
 assert not client.get('/api/profile/demo').json()['episodes']

def test_revisions_preserve_confirmed_sections_and_version(client):
 s=cafe(client)['session'];sid=s['session_id'];p=s['todays_look']
 confirmed=client.post('/api/full-look/confirm',json={'session_id':sid,'sections':['makeup'],'decision':'confirm','expected_version':p['version']}).json()['plan']
 before=confirmed['sections']['makeup']
 r=client.post('/api/full-look/revise',json={'session_id':sid,'user_request':'我今天穿黑色连衣裙','expected_version':confirmed['version']}).json()
 assert r['changed_sections']==['outfit'] and r['plan']['sections']['makeup']==before
 assert r['version']==confirmed['version']+1
 for text,domains in [('不扎头发',['hair']),('不喜欢甜香',['fragrance']),('我不想戴耳饰，也不想喷香水',['accessories','fragrance'])]:
  response=client.post('/api/full-look/revise',json={'session_id':sid,'user_request':text}).json()
  assert response['changed_sections']==domains
 p=response['plan'];assert p['sections']['accessories']['state']=='skipped' and p['sections']['fragrance']['state']=='skipped'
 assert client.post('/api/full-look/revise',json={'session_id':sid,'user_request':'不扎头发','expected_version':1}).status_code==409

def test_mode_switch_keeps_plan_and_step(client):
 s=cafe(client)['session'];sid=s['session_id']
 started=client.post('/api/chat',json={'session_id':sid,'message':'开始步骤'}).json()['session']
 changed=client.post('/api/chat',json={'session_id':sid,'message':'','experience_mode':'visual'}).json()['session']
 assert changed['session_id']==sid and changed['routine_step']==started['routine_step']
 assert changed['todays_look']==started['todays_look'] and changed['experience_mode']=='visual'

def test_material_memory_requires_explicit_choice(client):
 sid=cafe(client)['session']['session_id']
 client.post('/api/full-look/revise',json={'session_id':sid,'user_request':'我今天已经有棉质衬衫了'})
 r=client.post('/api/full-look/memory-candidate',json={'session_id':sid,'feedback':'下次记住我偏好的材质'})
 assert r.status_code==200
 assert r.json()['session']['memory_candidate']['material_preferences']==['cotton']
 assert client.get('/api/profile/demo').json()['episodes']==[]
 client.post('/api/chat',json={'session_id':sid,'message':'','action':'memory_consent','consent':False})
 assert client.get('/api/profile/demo').json()['episodes']==[]

def test_materials_are_scoped_and_not_composition_inference(client):
 r=client.post('/api/materials/explain',json={'material_ids':['satin','knit']})
 assert r.status_code==200
 assert all(row['kind']=='structure' for row in r.json()['results'])
 assert '纤维' in r.json()['message']
 assert client.post('/api/materials/explain',json={'material_ids':['unknown']}).status_code==404

def test_original_makeup_controls_camera_decline_and_overview(client):
 sid=cafe(client)['session']['session_id']
 client.post('/api/chat',json={'session_id':sid,'message':'开始步骤'})
 r=client.post('/api/chat',json={'session_id':sid,'message':'概览所有步骤'}).json()
 assert '准备' in r['message'] and r['session']['routine_step']==0
 client.post('/api/chat',json={'session_id':sid,'message':'帮我看看'})
 refused=client.post('/api/chat',json={'session_id':sid,'action':'camera_consent','consent':False}).json()
 assert not refused['session']['camera_consent'] and refused['session']['todays_look']

@pytest.mark.parametrize('text', ['这张照片看着像棉质衬衫，但我不知道成分', '我没有棉质衬衫', '不是棉质衬衫'])
def test_uncertain_or_negative_composition_stays_unknown(client,text):
 sid=cafe(client)['session']['session_id']
 result=client.post('/api/full-look/revise',json={'session_id':sid,'user_request':text}).json()
 outfit=result['plan']['sections']['outfit']
 assert outfit['materials']==[]
 assert '你确认已有' not in str(outfit)

@pytest.mark.parametrize('domain,text', [('skincare','请修改护肤与妆前：我不做妆前'),('makeup','请修改妆容：我想淡一点')])
def test_explicit_domain_edits_keep_makeup_routine_link(client,domain,text):
 sid=cafe(client)['session']['session_id']
 result=client.post('/api/full-look/revise',json={'session_id':sid,'user_request':text,'target_sections':[domain]}).json()
 assert result['changed_sections']==[domain]
 if domain=='makeup':
  assert result['plan']['sections']['makeup']['look_id']=='soft_formal'
  assert result['plan']['sections']['makeup']['routine_id']=='soft_formal_routine'


def test_bad_scope_does_not_mutate_and_restore_keeps_step(client):
 s=cafe(client)['session'];sid=s['session_id'];original=s['todays_look']
 assert client.post('/api/full-look/revise',json={'session_id':sid,'user_request':'黑色连衣裙','target_sections':['hair']}).status_code==409
 restored=client.get('/api/session/'+sid).json()
 assert restored['todays_look']==original and 'current_step' in restored

def test_explicit_material_memory_consent_persists_candidate(client):
 sid=cafe(client)['session']['session_id']
 client.post('/api/full-look/revise',json={'session_id':sid,'user_request':'我确认今天穿的是棉质衬衫'})
 candidate=client.post('/api/full-look/memory-candidate',json={
  'session_id':sid,'feedback':'下次优先考虑我确认过的棉材质'}).json()['session']
 before=client.get('/api/profile/demo').json()
 assert before['episodes']==[]
 saved=client.post('/api/chat',json={'session_id':sid,'message':'','action':'memory_consent','consent':True,
  'memory_candidate_id':candidate['memory_candidate_id'],'memory_candidate_version':candidate['memory_candidate_version']})
 assert saved.status_code==200
 profile=client.get('/api/profile/demo').json()
 assert profile['profile']['material_preferences']==['cotton'] and len(profile['episodes'])==1
