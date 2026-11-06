import pytest
from app.knowledge.tutorial_ingestion import TutorialImporter,TutorialSegment
from app.knowledge.repository import KnowledgeRepository

def test_rights_review_and_deduplication(tmp_path):
    repo=KnowledgeRepository(tmp_path/'knowledge')
    importer=TutorialImporter(repo,{'owned':{'permission':'original','publisher':'TRACE','evidence':'Original text supplied by the author'}})
    item={'source_id':'owned','title':'One action','text':'Ask for one action, then wait for confirmation.','language':'en','tags':['accessibility']}
    result=importer.import_segments([item],commit=True)
    assert result['accepted']==1
    row=repo.all()['ACCESSIBILITY_GUIDANCE'][0]
    assert row['verified'] is False and row['status']=='DRAFT'
    assert importer.import_segments([item],commit=True)['duplicates']==1
    with pytest.raises(PermissionError):TutorialImporter(repo,{'no':{'permission':'citation_only'}}).import_segments([{**item,'source_id':'no'}])
    with pytest.raises(PermissionError):importer.import_segments([{**item,'source_id':'not_allowlisted'}])

def test_timestamped_video_text_requires_rights_and_never_ingests_video():
    with pytest.raises(ValueError):TutorialSegment.model_validate({'source_id':'x','title':'x','text':'x','language':'en','start_seconds':20,'end_seconds':10})
    with pytest.raises(ValueError):TutorialSegment.model_validate({'source_id':'x','title':'x','text':'x','language':'en','video':'full-recording'})
