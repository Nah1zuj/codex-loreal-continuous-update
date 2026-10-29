import re
from test_v4_full_look import client

def test_english_chat_and_steps_keep_all_known_guidance(client):
 r=client.post('/api/chat',json={'message':'cafe meeting formal and natural','locale':'en'}).json()
 assert not re.search(r'[\u3400-\u9fff]',r['message'])
 assert 'choice' in r['message'].lower()
 sid=r['session']['session_id']
 step=client.post('/api/chat',json={'session_id':sid,'message':'start routine','locale':'en'}).json()
 assert 'blend' in step['step']['instruction']
 assert 'base' in step['step']['instruction']
 assert not re.search(r'[\u3400-\u9fff]',step['step']['instruction'])

def test_chinese_default_and_unknown_original_are_honest(client):
 r=client.post('/api/chat',json={'message':''}).json()
 assert '今天' in r['message']
 from app.content.locale import translate
 assert translate('未审核的新文本','en')=='Original text (translation unavailable): 未审核的新文本'

def test_versioned_rules_have_independent_examples_and_negative_cases():
 from app.policies.registry import PolicyRegistry
 rules=PolicyRegistry().system('accessibility_policy','brand_copy_policy')
 for rule in ['先给出清楚可执行的动作','最多','Never imitate an author','at most one short reflective sentence','Rejected example','反例','not fine-tuning or training']:
  assert rule in rules
 # This checks authored policy examples, not model accuracy.
 assert 'You must feel insecure; I will cure your anxiety' in rules
 assert '编造内心' in rules

def test_generated_routine_material_and_cafe_catalog_has_no_untranslated_chinese(client):
 from app.content.locale import translate
 from app.config import ROOT
 import json
 routines=json.loads((ROOT/'data/demo/knowledge/routines.json').read_text(encoding='utf-8'))['records']
 for routine in routines:
  for step in routine['steps']:
   for field in ['name','instruction','instruction_slow','instruction_repeat','explanation_why']:
    assert not re.search(r'[\u3400-\u9fff]',translate(step[field],'en'))
 materials=client.get('/api/materials').json()['results']
 for row in materials:
  for field in ['texture_description','weight_drape','breathability_notes','care_notes']:
   assert not re.search(r'[\u3400-\u9fff]',translate(row[field],'en'))
 r=client.post('/api/chat',json={'message':'cafe meeting formal and natural','locale':'en'}).json()
 for section in r['session']['todays_look']['sections'].values():
  for suggestion in section['suggestions']:
   assert not re.search(r'[\u3400-\u9fff]',suggestion['reason'])
 assert re.search(r'[\u3400-\u9fff]',r['canonical']['message'])

def test_all_demo_reading_and_visual_messages_keep_safety_in_english(client):
 from app.content.locale import translate
 from app.reading.service import ReadingService
 from app.config import Settings
 from app.vision.language import accessible_result
 settings=Settings(reading_provider='mock',developer_mode=True,allow_remote_ai=False)
 reader=ReadingService(settings)
 for kind in ['product','garment']:
  for demo in [True,False]:
   result=reader.read(b'',demo=demo,label_kind=kind)
   for key in ['summary','composition','shade','instructions','full_text']:
    if result.get(key):assert not re.search(r'[\u3400-\u9fff]',translate(result[key],'en'))
 for status in ['BOTH','NO_BLUSH','LEFT_ONLY','RIGHT_ONLY','APPLIED','NOT_APPLIED','OBVIOUS_OVERFLOW','UNCERTAIN']:
  message=accessible_result({'status':status,'confidence':.99,'simulated':True},settings)
  english=translate(message,'en')
  assert not re.search(r'[\u3400-\u9fff]',english)
  assert 'Simulated' in english
 response=client.post('/api/materials/explain',json={'material_ids':['cotton','linen']}).json()
 english=translate(response['message'],'en')
 assert not re.search(r'[\u3400-\u9fff]',english)
 assert 'Appearance' in english
