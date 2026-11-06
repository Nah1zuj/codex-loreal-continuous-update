import base64
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.config import Settings
from app.main import create_app
from app.services.model_client import RemoteModelClient


def label_image():
    with BytesIO() as output:
        Image.new('RGB', (96, 64), 'white').save(output, format='PNG')
        return 'data:image/png;base64,' + base64.b64encode(output.getvalue()).decode()


def test_six_domain_selection_and_revision_preserve_active_lesson(tmp_path):
    with TestClient(create_app(Settings(memory_path=tmp_path/'look.sqlite'))) as client:
        selected = client.post('/api/chat', json={'message':'cafe meeting formal and natural'}).json()['session']
        sid = selected['session_id']
        s = client.post('/api/chat', json={'session_id':sid,'message':'开始步骤'}).json()['session']
        p = s['todays_look']
        assert len(p['sections']) == 6
        for domain, section in p['sections'].items():
            assert section['unknowns']
            decision = {
                'session_id':sid, 'sections':[domain], 'decision':'select',
                'suggestion_id':section['suggestions'][-1]['id'], 'expected_version':p['version'],
            }
            selected_option = client.post('/api/full-look/confirm', json=decision).json()['plan']
            assert selected_option['sections'][domain]['selected_suggestion_id'] == decision['suggestion_id']
            decision.pop('suggestion_id')
            decision.update(decision='confirm', expected_version=selected_option['version'])
            p = client.post('/api/full-look/confirm', json=decision).json()['plan']
            assert domain in p['user_confirmed_sections']

        updates = [
            {'session_id':sid,'target_sections':['makeup'],'user_request':'妆容我想淡一点','expected_version':p['version']},
            {'session_id':sid,'target_sections':['hair'],'user_request':'不扎头发','expected_version':p['version']},
        ]
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda body:client.post('/api/full-look/revise',json=body),updates))
        assert sorted(result.status_code for result in results) == [200,409]
        accepted = next(result.json() for result in results if result.status_code==200)
        rejected = next(result.json()['detail'] for result in results if result.status_code==409)
        assert rejected['code']=='FULL_LOOK_CONFLICT' and rejected['current_version']==p['version']+1
        changed = accepted['changed_sections'][0]
        assert accepted['session']['makeup_plan'] == s['makeup_plan']
        assert accepted['plan']['sections'][changed]['state']=='proposed'
        assert all(accepted['plan']['sections'][key]==p['sections'][key] for key in p['sections'] if key!=changed)

        skip = {'session_id':sid,'sections':['fragrance'],'decision':'skip','expected_version':accepted['version']}
        skipped = client.post('/api/full-look/confirm',json=skip).json()['plan']
        assert skipped['sections']['fragrance']['state']=='skipped'
        assert 'fragrance' not in skipped['user_confirmed_sections']


def test_label_denial_and_wrong_provider_never_call_transport(tmp_path, monkeypatch):
    requests = []
    def fake_read(self, model, system, content):
        requests.append((self.provider,model,content))
        return {'full_text':'Label ABC\nFiber: 1[unknown]0% cotton','confidence':.98,
                'uncertain_characters':['[unknown]'],'composition':'100% cotton'}
    monkeypatch.setattr(RemoteModelClient,'chat_json',fake_read)
    settings = Settings(memory_path=tmp_path/'label.sqlite',reading_provider='qwen',
                        allow_remote_ai=True,api_key='fake-key-for-transport-test')
    with TestClient(create_app(settings)) as client:
        metadata = client.get('/api/reading/availability').json()
        assert metadata['status']=='configured' and metadata['remote_verified'] is False
        assert metadata['service_name']=='Alibaba Cloud Model Studio (Qwen)'
        body = {'image':label_image(),'label_kind':'garment','explicit_consent':True}
        assert client.post('/api/reading/read',json=body).status_code==403
        mismatched = {**body,'remote_upload_consent':True,'authorized_provider':'deepseek'}
        assert client.post('/api/reading/read',json=mismatched).status_code==403
        assert requests == []

        allowed = {**mismatched,'authorized_provider':'qwen'}
        result = client.post('/api/reading/read',json=allowed)
        assert result.status_code==200, result.text
        assert len(requests)==1 and requests[0][0]=='qwen'
        assert requests[0][2][0]['image_url']['url'].startswith('data:image/jpeg;base64,')
        data = result.json()
        assert data['status']=='UNCERTAIN' and data['full_text']=='Label ABC\nFiber: 1[unknown]0% cotton'
        assert data['uncertain_characters']==['[unknown]'] and data['composition'] is None


def test_label_configuration_gap_and_verbatim_fields(tmp_path, monkeypatch):
    calls = []
    def fake_read(self, model, system, content):
        calls.append(self.provider)
        return {'full_text':'Test label\nShade 02\nApply sparingly','confidence':.98,
                'shade':'20','instructions':'Apply sparingly'}
    monkeypatch.setattr(RemoteModelClient,'chat_json',fake_read)
    settings = Settings(memory_path=tmp_path/'missing.sqlite',reading_provider='qwen',allow_remote_ai=True,api_key='')
    body = {'image':label_image(),'explicit_consent':True,'remote_upload_consent':True,'authorized_provider':'qwen'}
    with TestClient(create_app(settings)) as client:
        assert client.get('/api/reading/availability').json()['status']=='missing_configuration'
        blocked = client.post('/api/reading/read',json=body)
        assert blocked.status_code==503 and blocked.json()['detail']['code']=='LABEL_PROVIDER_UNAVAILABLE'
        assert calls==[]
    settings.api_key = 'dummy'
    with TestClient(create_app(settings)) as client:
        output = client.post('/api/reading/read',json=body).json()
        assert output['status']=='READ' and output['instructions']=='Apply sparingly'
        assert output['full_text']=='Test label\nShade 02\nApply sparingly'
        assert output['shade'] is None and output['composition'] is None


def test_product_comparison_identifies_source_example_and_unavailable(tmp_path):
    with TestClient(create_app(Settings(memory_path=tmp_path/'products.sqlite'))) as client:
        catalogue = client.get('/api/products/catalog').json()['results']
        assert {item['product_id'] for item in catalogue} >= {'maybelline_matte_ink','maybelline_vinyl_ink'}
        response = client.post('/api/products/compare',json=['maybelline_matte_ink','maybelline_vinyl_ink','sample_01','unknown'])
        first,second,demo,unknown = response.json()['results']
        assert first['attributes']['finish']=='matte' and second['attributes']['finish']=='glossy'
        for row in (first,second):
            assert row['review_status']=='DRAFT' and row['evidence_kind']=='source'
            assert row['attributes']['undertone'] is None
            assert row['sources'][0]['url'].startswith('https://www.maybelline.com/lip-makeup/lipstick/')
        assert demo['evidence_kind']=='demo' and demo['sources']==[]
        assert unknown['evidence_kind']=='unavailable' and not unknown['attributes']
