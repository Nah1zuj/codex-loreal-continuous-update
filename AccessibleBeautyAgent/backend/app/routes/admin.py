import base64
import uuid
from fastapi import APIRouter,Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel,Field,StrictBool
from app.schemas.models import SearchRequest
from app.schemas.knowledge import MODELS,IDS
from app.knowledge.vocabulary import Vocabulary
from app.knowledge.repository import atomic_json
from app.knowledge.importer import import_file

class SaveRecord(BaseModel):
    record:dict
    expected_version:int|None=None
    reviewed:StrictBool=False
    reviewer:str|None=None
class VersionRequest(BaseModel):expected_version:int=Field(ge=1)
class UploadReference(BaseModel):
    filename:str=Field(max_length=200)
    look_id:str
    image:str=Field(max_length=14_000_000)
    demo_data:StrictBool=False
class RebuildRequest(BaseModel):
    type:str|None=None
    look_id:str|None=None
class ImportRequest(BaseModel):
    filename:str=Field(max_length=200)
    file:str=Field(max_length=22_000_000)
    type:str|None=None
    commit:StrictBool=False
class TutorialImportRequest(BaseModel):
    segments:list[dict]=Field(min_length=1,max_length=500)
    commit:StrictBool=False

def build_admin_router(service,settings):
    def enabled():
        if not settings.admin_enabled:raise PermissionError('内部知识管理已关闭（ADMIN_ENABLED=false）。')
    router=APIRouter(prefix='/api/admin',dependencies=[Depends(enabled)])
    @router.post('/tutorials/import')
    def tutorial_import(body:TutorialImportRequest):
        import json
        from app.config import ROOT
        from app.knowledge.tutorial_ingestion import TutorialImporter
        registry=json.loads((ROOT/'data/config/knowledge_sources.json').read_text(encoding='utf-8'))
        return TutorialImporter(service.repository,registry).import_segments(body.segments,body.commit)
    @router.get('/dashboard')
    def dashboard():return service.dashboard()
    @router.get('/vocabulary')
    def vocabulary():return Vocabulary().values
    @router.get('/schemas')
    def schemas():return {k:m.model_json_schema() for k,m in MODELS.items()}
    @router.get('/records/{kind}')
    def records(kind:str):
        if kind not in MODELS:raise KeyError('Unknown knowledge type')
        return {'records':service.repository.all()[kind],'id_field':IDS[kind]}
    @router.post('/records/{kind}')
    def save(kind:str,body:SaveRecord):
        record=service.repository.save(kind,body.record,body.expected_version,body.reviewed,body.reviewer)
        if kind=='REFERENCE_CASE' and record['human_verified']:
            atomic_json(settings.media_dir/'verified'/f'{record["reference_id"]}_v{record["version"]}.json',record)
        return {'record':record,'message':'已保存并通过人工审核。请重建索引。' if body.reviewed else '已保存草稿。'}
    @router.post('/records/{kind}/{record_id}/deprecate')
    def deprecate(kind:str,record_id:str,body:VersionRequest):return {'record':service.repository.deprecate(kind,record_id,body.expected_version)}
    @router.post('/validate')
    def validate():
        report=service.repository.validate();return {k:v for k,v in report.items() if k!='records'}
    @router.post('/rebuild')
    def rebuild(body:RebuildRequest):return service.rebuild(body.type,body.look_id)
    @router.post('/smoke')
    def smoke():return service.smoke()
    @router.post('/rag/search')
    def rag(body:SearchRequest):return service.agent.retriever.debug_search(body.query,body.filters,body.limit)
    @router.post('/references/upload')
    def upload(body:UploadReference):return {'record':service.upload(body.filename,body.look_id,body.image,demo_data=body.demo_data)}
    @router.post('/references/{reference_id}/analyze')
    def analyze(reference_id:str,body:VersionRequest):return service.analyze(reference_id,body.expected_version)
    @router.get('/reference-media/{reference_id}')
    def media(reference_id:str):return FileResponse(service.image_path(service.repository.get('REFERENCE_CASE',reference_id)),media_type='image/jpeg')
    @router.post('/import')
    def import_data(body:ImportRequest):
        from pathlib import Path
        extension=Path(body.filename).suffix.lower()
        if extension not in ('.csv','.xlsx'):raise ValueError('只支持 CSV / XLSX。')
        raw=base64.b64decode(body.file.split(',',1)[-1],validate=True)
        destination=settings.knowledge_dir.parent/'import'/f'{uuid.uuid4().hex}{extension}'
        destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(raw)
        report=import_file(destination,service.repository,body.type,body.commit)
        atomic_json(settings.reports_dir/(report['report_id']+'.json'),report)
        return report
    return router
