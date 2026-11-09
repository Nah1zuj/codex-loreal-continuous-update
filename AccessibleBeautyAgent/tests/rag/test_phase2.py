import csv
import json
import shutil
import io
import base64
from pathlib import Path
import pytest
from PIL import Image
from fastapi.testclient import TestClient

@pytest.fixture
def kbdir(tmp_path):
    from app.config import ROOT
    path=tmp_path/'knowledge'
    shutil.copytree(ROOT/'data/demo/knowledge',path)
    (path/'sources.json').write_text('{"records":[]}',encoding='utf-8')
    return path

@pytest.fixture
def repository(kbdir):
    from app.knowledge.repository import KnowledgeRepository
    return KnowledgeRepository(kbdir,history_dir=kbdir.parent/'history')

def test_invalid_look():
    from app.schemas.knowledge import BeautyLook
    with pytest.raises(ValueError):BeautyLook.model_validate({'look_id':'test'})

def test_broken_reference(kbdir):
    from app.rag.knowledge import KnowledgeStore
    path=kbdir/'reference_cases.json'
    content=json.loads(path.read_text(encoding='utf-8'))
    content['records'][0]['look_id']='missing'
    path.write_text(json.dumps(content),encoding='utf-8')
    with pytest.raises(ValueError,match='look'):KnowledgeStore(kbdir)

def test_duplicate_id(kbdir):
    from app.rag.knowledge import KnowledgeStore
    path=kbdir/'looks.json';content=json.loads(path.read_text(encoding='utf-8'))
    content['records'].append(content['records'][0])
    path.write_text(json.dumps(content),encoding='utf-8')
    with pytest.raises(ValueError,match='Duplicate'):KnowledgeStore(kbdir)

def test_verified_protected(repository):
    record=repository.get('REFERENCE_CASE','soft_formal_ref_001')
    verified=repository.save('REFERENCE_CASE',record,expected_version=record['version'],reviewed=True,reviewer='Test reviewer')
    assert verified['human_verified'] and verified['verified']
    changed={**verified,'notes':'automated replacement'}
    with pytest.raises(PermissionError):repository.save('REFERENCE_CASE',changed,expected_version=verified['version'],automated=True)
    assert repository.get('REFERENCE_CASE',record['reference_id'])['notes']==verified['notes']

def test_stale_version_rejected(repository):
    record=repository.get('PRODUCT','sample_01')
    saved=repository.save('PRODUCT',record,expected_version=record['version'])
    with pytest.raises(ValueError,match='version'):repository.save('PRODUCT',record,expected_version=record['version'])
    assert saved['version']==record['version']+1

def test_only_verified_production_documents(kbdir):
    from app.rag.knowledge import KnowledgeStore
    from app.config import Settings
    from app.rag.retriever import HybridRetriever
    store=KnowledgeStore(kbdir)
    settings=Settings(developer_mode=False,research_mode=False)
    rag=HybridRetriever(store,settings)
    assert rag.search('dinner')['results']==[]
    # Even an explicit false filter must not weaken production policy.
    assert rag.search('dinner',{'verified':'false'})['results']==[]

def test_verified_reference_filter(repository,kbdir):
    from app.rag.knowledge import KnowledgeStore
    from app.rag.retriever import HybridRetriever
    from app.config import Settings
    record=repository.get('REFERENCE_CASE','soft_formal_ref_001')
    repository.save('REFERENCE_CASE',record,expected_version=record['version'],reviewed=True,reviewer='Tester')
    rag=HybridRetriever(KnowledgeStore(kbdir),Settings(developer_mode=True))
    result=rag.search('Soft Formal dinner blush',{'look_id':'soft_formal','document_type':'REFERENCE_CASE','verified':'true'})
    assert result['results'] and all(d['metadata']['verified'] for d in result['results'])

def test_csv_missing_fields_reported(repository,tmp_path):
    from app.knowledge.importer import import_file
    path=tmp_path/'products.csv'
    path.write_text('product_id,name,category\nnew_product,,lip\n',encoding='utf-8')
    report=import_file(path,repository,kind='PRODUCT',commit=True)
    assert report['total_rows']==1 and report['rejected']==1
    assert any(e['field']=='name' for e in report['errors'])

def test_index_rebuild_preserves_canonical(kbdir):
    from app.rag.knowledge import KnowledgeStore
    from app.rag.retriever import HybridRetriever
    from app.config import Settings
    before={p.name:p.read_bytes() for p in kbdir.glob('*.json')}
    rag=HybridRetriever(KnowledgeStore(kbdir),Settings(developer_mode=True))
    rag.persist(kbdir.parent/'index.json')
    assert before=={p.name:p.read_bytes() for p in kbdir.glob('*.json')}
    ids={d['document_id'] for d in rag.documents}
    assert all(not d['metadata']['parent_id'] or d['metadata']['parent_id'] in ids for d in rag.documents)

def test_dinner_debug_returns_channels(kbdir):
    from app.rag.knowledge import KnowledgeStore
    from app.rag.retriever import HybridRetriever
    from app.config import Settings
    rag=HybridRetriever(KnowledgeStore(kbdir),Settings(developer_mode=True))
    result=rag.debug_search('今晚 dinner，正式一点但不要太成熟')
    assert result['parsed_filters']['scene']=='dinner'
    assert all(x in result for x in ('semantic_results','lexical_results','merged_results','reranked_results'))
    assert any(x['metadata'].get('look_id')=='soft_formal' for x in result['results'])

def test_upload_verify_and_rebuild(kbdir):
    from app.main import create_app
    from app.config import Settings
    settings=Settings(knowledge_dir=kbdir,memory_path=kbdir.parent/'memory.sqlite',index_path=kbdir.parent/'index.json',developer_mode=True,media_dir=kbdir.parent/'references',history_dir=kbdir.parent/'history',allow_remote_ai=False)
    app=create_app(settings)
    buffer=io.BytesIO();Image.new('RGB',(300,300),(120,110,100)).save(buffer,format='JPEG')
    with TestClient(app) as client:
        r=client.post('/api/admin/references/upload',json={'filename':'test.jpg','look_id':'soft_formal','image':base64.b64encode(buffer.getvalue()).decode()})
        assert r.status_code==200,r.text
        ref=r.json()['record']
        r=client.post(f"/api/admin/references/{ref['reference_id']}/analyze",json={'expected_version':ref['version']})
        assert r.status_code==200,r.text
        draft=r.json()['record'];assert not draft['human_verified']
        draft['blush']['intensity']='light_medium'
        r=client.post('/api/admin/records/REFERENCE_CASE',json={'record':draft,'expected_version':draft['version'],'reviewed':True,'reviewer':'Human tester'})
        assert r.status_code==200,r.text
        assert r.json()['record']['human_verified']
        assert client.post('/api/admin/rebuild',json={}).status_code==200
        r=client.post('/api/admin/rag/search',json={'query':'dinner blush','filters':{'look_id':'soft_formal','verified':'true'}})
        assert r.status_code==200,r.text
        assert any(x['document_type']=='REFERENCE_CASE' for x in r.json()['results'])
