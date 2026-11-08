"""Rights-controlled local text ingestion into the existing canonical KB.

No crawling, audio/video downloading or automatic human-review promotion.
"""
import hashlib,json
from datetime import datetime,timezone
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,model_validator
from app.schemas.knowledge import AccessibilityGuidance,SourceRecord,MODELS

class TutorialSegment(BaseModel):
    model_config=ConfigDict(extra='forbid')
    source_id:str=Field(pattern=r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,119}$')
    title:str=Field(min_length=1,max_length=200)
    text:str=Field(min_length=1,max_length=8000)
    language:Literal['zh-CN','en']
    tags:list[str]=Field(default_factory=list,max_length=20)
    start_seconds:float|None=Field(default=None,ge=0)
    end_seconds:float|None=Field(default=None,ge=0)
    @model_validator(mode='after')
    def timestamps(self):
        if (self.start_seconds is None)!=(self.end_seconds is None) or (self.start_seconds is not None and self.end_seconds<=self.start_seconds):raise ValueError('Invalid transcript segment timestamps')
        return self

class TutorialImporter:
    def __init__(self,repository,registry):self.repository=repository;self.registry=registry
    def import_segments(self,segments,commit=False):
        if not 1<=len(segments)<=500:raise ValueError('Import 1–500 segments at a time')
        current=self.repository.all();staged={kind:[] for kind in MODELS}
        ids={r['guidance_id'] for r in current['ACCESSIBILITY_GUIDANCE']};sources={r['source_id'] for r in current['SOURCE']};duplicates=0
        for raw in segments:
            item=TutorialSegment.model_validate(raw);source=self.registry.get(item.source_id)
            if not source or source.get('permission') not in {'original','cc-by','cc0','licensed'} or not source.get('evidence'):raise PermissionError('Source is not allowlisted with reusable text rights and evidence')
            if item.source_id not in sources:
                staged['SOURCE'].append(SourceRecord(source_id=item.source_id,title=source.get('title',item.source_id),creator=source.get('publisher'),url=source.get('url'),local_file=source.get('local_file'),source_type='original' if source['permission']=='original' else 'licensed_text',use_permission=source['permission'],use_basis=source['evidence'],notes=json.dumps({'permission':source['permission'],'evidence':source['evidence'],'attribution':source.get('attribution'),'accessed_at':datetime.now(timezone.utc).isoformat()},ensure_ascii=False)).model_dump(mode='json'));sources.add(item.source_id)
            digest=hashlib.sha256((item.source_id+'\n'+item.language+'\n'+' '.join(item.text.split())).encode()).hexdigest()[:24]
            gid='tutorial_'+digest
            if gid in ids:duplicates+=1;continue
            ids.add(gid)
            metadata=json.dumps({'title':item.title,'language':item.language,'start_seconds':item.start_seconds,'end_seconds':item.end_seconds,'processing_version':1,'permissions':source['permission']},ensure_ascii=False)
            staged['ACCESSIBILITY_GUIDANCE'].append(AccessibilityGuidance(guidance_id=gid,category='tutorial_segment',principle=item.title,description=item.text,source=item.source_id,source_ids=[item.source_id],source_type='original' if source['permission']=='original' else 'licensed_text',review_notes=metadata,tags=[item.language,*item.tags],verified=False,demo_data=False,status='DRAFT').model_dump(mode='json'))
        if commit:self.repository.commit_import(staged)
        return {'accepted':len(staged['ACCESSIBILITY_GUIDANCE']),'duplicates':duplicates,'committed':commit,'records':staged,'review_required':True}
