from test_phase2 import kbdir,repository
import pytest

def test_external_requests_disabled():
    from app.services.model_client import RemoteModelClient
    from app.config import Settings
    with pytest.raises(PermissionError,match='ALLOW_REMOTE_AI'):
        RemoteModelClient(Settings(allow_remote_ai=False),'deepseek').request('/chat/completions',{})

def test_missing_source_is_an_error(repository):
    r=repository.get('PRODUCT','sample_01');r['source_ids']=['missing']
    with pytest.raises(ValueError,match='source'):repository.save('PRODUCT',r,expected_version=r['version'])

def test_invalid_url():
    from app.schemas.knowledge import SourceRecord
    with pytest.raises(ValueError):SourceRecord(source_id='bad_source',title='bad',url='javascript:alert(1)')

def test_nested_unknown_field_not_silently_discarded():
    from app.schemas.knowledge import BeautyLook
    with pytest.raises(ValueError):BeautyLook(look_id='test',name='Test',blush={'intensitty':'medium'})

def test_csv_duplicates_not_overwritten(repository,tmp_path):
    from app.knowledge.importer import import_file
    p=tmp_path/'products.csv';p.write_text('product_id,brand,category\nsample_01,replacement,lip\n',encoding='utf-8')
    before=repository.get('PRODUCT','sample_01')
    report=import_file(p,repository,kind='PRODUCT',commit=True)
    assert report['rejected']==1
    assert repository.get('PRODUCT','sample_01')==before

def test_unknown_vocabulary_is_visible_warning(repository):
    from app.knowledge.validation import validate_records
    records=repository.all();records['PRODUCT'][0]['finish']='my_new_finish'
    report=validate_records(records)
    assert report['errors']==[]
    assert any(w['field']=='finish' and 'my_new_finish' in w['message'] for w in report['warnings'])

def test_deprecated_excluded_even_developer(repository,kbdir):
    from app.rag.knowledge import KnowledgeStore
    from app.rag.retriever import HybridRetriever
    from app.config import Settings
    r=repository.get('REFERENCE_CASE','soft_formal_ref_001')
    repository.deprecate('REFERENCE_CASE',r['reference_id'],r['version'])
    rag=HybridRetriever(KnowledgeStore(kbdir),Settings(developer_mode=True))
    assert rag.search('dinner',{'document_type':'REFERENCE_CASE'})['results']==[]

def test_production_look_tools_do_not_use_drafts(kbdir):
    from app.config import Settings
    from app.rag.knowledge import KnowledgeStore
    from app.looks.service import LookService
    assert LookService(KnowledgeStore(kbdir),Settings(developer_mode=False,research_mode=False)).search('dinner',['polished'],[],{})==[]

def test_history_retains_previous_version(repository):
    r=repository.get('PRODUCT','sample_01');r['name']='new label'
    repository.save('PRODUCT',r,expected_version=r['version'])
    assert len(list((repository.history_dir/'PRODUCT').glob('sample_01_v1_*.json')))==1


def test_reranker_cannot_inject_or_edit_knowledge(kbdir):
    from app.rag.knowledge import KnowledgeStore
    from app.rag.retriever import HybridRetriever
    from app.config import Settings
    class Untrusted:
        def rerank(self,query,rows):
            return [{**rows[0],'content':'tampered'}, {'document_id':'injected','content':'unsafe'}]
    rag=HybridRetriever(KnowledgeStore(kbdir),Settings(developer_mode=True),reranker=Untrusted())
    result=rag.search('dinner')['results']
    assert len(result)==1 and result[0]['content']!='tampered'


def test_xlsx_template_roundtrip(repository):
    from app.config import ROOT
    from app.knowledge.importer import import_file
    report=import_file(ROOT/'templates/beauty_kb_template.xlsx',repository,commit=True)
    assert report['total_rows']==7 and report['accepted']==7 and report['rejected']==0
    assert repository.get('LOOK','template_look')['verified'] is False
    assert len(repository.get('ROUTINE','template_routine')['steps'])==1


def test_video_extract_selected_frames(tmp_path):
    import sys
    from app.config import ROOT
    sys.path.insert(0,str(ROOT/'scripts'))
    from extract_video_frames import extract
    import cv2
    import numpy as np
    file=tmp_path/'test.avi'
    writer=cv2.VideoWriter(str(file),cv2.VideoWriter_fourcc(*'MJPG'),10,(100,100))
    assert writer.isOpened()
    for n in range(20):writer.write(np.full((100,100,3),n*10,dtype=np.uint8))
    writer.release()
    report=extract(file,tmp_path/'frames',timestamps='0,1,9')
    assert len(report['frames'])==2 and len(report['errors'])==1
    assert report['ai_called'] is False


def test_canonical_routine_list_replaces_legacy_link():
    from app.schemas.knowledge import BeautyLook
    look=BeautyLook(look_id='x',name='X',routine_id='old',routine_ids=['new'])
    assert look.routine_id=='new' and look.routine_ids==['new']
    cleared=BeautyLook(look_id='x',name='X',routine_id='old',routine_ids=[])
    assert cleared.routine_id is None
    assert BeautyLook(look_id='x',name='X',routine_id='old').routine_ids==['old']


def test_guidance_edit_updates_index_content():
    from app.schemas.knowledge import AccessibilityGuidance
    guidance=AccessibilityGuidance(guidance_id='x',description='new',content='old')
    assert guidance.content=='new'


def test_running_session_rechecks_deprecated_routine(kbdir):
    from app.main import create_app
    from app.config import Settings
    from app.schemas.models import Stage
    settings=Settings(knowledge_dir=kbdir,memory_path=kbdir.parent/'session.sqlite',index_path=kbdir.parent/'index.json',media_dir=kbdir.parent/'media',history_dir=kbdir.parent/'history',developer_mode=True)
    app=create_app(settings);agent=app.state.agent
    session=agent.sessions.create('demo');session.stage=Stage.LOOK_SELECTED;session.selected_look='soft_formal';session.routine_id='soft_formal_routine'
    agent.start_routine(session.routine_id,session)
    agent.store.routine_map[session.routine_id]['status']='DEPRECATED'
    with pytest.raises(ValueError,match='重新'):agent.current_step(session)
    assert not session.routine_started and not session.camera_consent
    session.stage=Stage.LOOK_SELECTED;session.selected_look='soft_formal'
    with pytest.raises(ValueError):agent.start_routine('soft_formal_routine',session)


def test_unknown_step_field_reported():
    from app.schemas.knowledge import RoutineStep
    with pytest.raises(ValueError):RoutineStep(step_id='x',instruction='action',instructon='typo')
