import base64
import io
import uuid
from pathlib import Path
from PIL import Image
from app.config import ROOT
from app.schemas.knowledge import MODELS,IDS,SourceRecord,ReferenceCase
from app.knowledge.repository import KnowledgeRepository,atomic_json,now
from app.rag.knowledge import KnowledgeStore
from app.rag.retriever import HybridRetriever
from app.vision.reference import reference_analyzer

class KnowledgeAdminService:
    def __init__(self,agent,settings):
        self.agent=agent;self.settings=settings
        self.repository=KnowledgeRepository(settings.knowledge_dir,settings.history_dir)
        self.analyzer=reference_analyzer(settings)
    def dashboard(self):
        data=self.repository.all();references=data['REFERENCE_CASE']
        indexed={d['metadata'].get('look_id') for d in self.agent.retriever.documents}
        versions={d['document_id']:d['metadata']['version'] for d in self.agent.retriever.documents if d['document_type']=='REFERENCE_CASE'}
        return {'counts':{k:len(v) for k,v in data.items()},'verified_references':sum(r['human_verified'] for r in references),'unverified_references':sum(not r['human_verified'] for r in references),'rag_documents':len(self.agent.retriever.documents),'remote_ai_enabled':self.settings.allow_remote_ai,'reference_provider':self.settings.reference_provider,'records':data,'indexed_looks':sorted(x for x in indexed if x),'indexed_versions':versions}
    def rebuild(self,kind=None,look_id=None):
        with self.agent.sessions.lock,self.repository.lock:
            report=self.repository.validate()
            if report['errors']:raise ValueError('请先修复校验错误：'+str(report['errors']))
            store=KnowledgeStore(self.settings.knowledge_dir);index=HybridRetriever(store,self.settings)
            index.persist(self.settings.index_path)
            self.agent.store=store;self.agent.looks.store=store;self.agent.products.store=store;self.agent.retriever=index
            scoped=[d for d in index.documents if (not kind or d['document_type']==kind) and (not look_id or d['metadata']['look_id']==look_id)]
            return {'status':'PASS','documents':len(index.documents),'scope_documents':len(scoped),'scope':{'type':kind,'look_id':look_id},'note':'为保留其他知识，原子重建完整索引；scope 只限定报告计数。','smoke':self.smoke()}
    def smoke(self):
        result=self.agent.retriever.debug_search('今晚 dinner，正式一点但不要太成熟',limit=20)
        available=bool(result['results'])
        return {'status':'PASS' if available else 'WARNING','message':'检索返回了知识文档。' if available else '当前过滤条件下没有可用的已审核知识，请先审核 Look、流程和参考。','results':result['results'][:5]}
    def image_path(self,record):
        path=(ROOT/record['source_file']).resolve()
        if not path.is_relative_to(self.settings.media_dir.resolve()):raise PermissionError('图片必须位于配置的 references 目录。')
        if not path.is_file():raise KeyError('Reference image file not found')
        return path
    def upload(self,filename,look_id,encoded,reference_id=None,demo_data=False):
        self.repository.get('LOOK',look_id)
        if len(encoded)>14_000_000:raise ValueError('图片太大，请控制在 10MB 内。')
        try:
            raw=base64.b64decode(encoded.split(',',1)[-1],validate=True)
            with Image.open(io.BytesIO(raw)) as image:
                if image.format not in ('JPEG','PNG','WEBP') or image.width*image.height>25_000_000:raise ValueError('只支持 JPEG/PNG/WebP，像素总量不超过 2500 万。')
                image=image.convert('RGB');image.thumbnail((1600,1600))
                buffer=io.BytesIO();image.save(buffer,format='JPEG',quality=90)
        except (OSError,ValueError) as exc:raise ValueError('图片无法读取，请使用有效 JPEG/PNG/WebP。') from exc
        uid=uuid.uuid4().hex
        path=self.settings.media_dir/'raw'/f'{uid}.jpg';path.parent.mkdir(parents=True,exist_ok=True)
        relative=str(path.relative_to(ROOT)).replace('\\','/')
        source=SourceRecord(source_id='source_'+uid,title=Path(filename).name,source_type='team_reference',local_file=relative,demo_data=demo_data).model_dump(mode='json')
        look=self.repository.get('LOOK',look_id)
        record=ReferenceCase(reference_id=reference_id or 'ref_'+uid,look_id=look_id,source_file=relative,source_id=source['source_id'],scene=look['scene'],status='RAW',source_type='team_reference',demo_data=demo_data).model_dump(mode='json')
        path.write_bytes(buffer.getvalue())
        try:self.repository.commit_import({'SOURCE':[source],'REFERENCE_CASE':[record]})
        except Exception:
            path.unlink();raise
        return record
    def analyze(self,reference_id,expected_version):
        with self.repository.lock:
            record=self.repository.get('REFERENCE_CASE',reference_id)
            if record['version']!=expected_version:raise ValueError('version conflict / 请重新加载。')
            with Image.open(self.image_path(record)) as image:
                image=image.convert('RGB');image.thumbnail((1024,1024));buffer=io.BytesIO();image.save(buffer,format='JPEG',quality=85)
            analysis=self.analyzer.analyze(buffer.getvalue())
            allowed={'overall','base','blush','lip','eye','quality','confidence','uncertainty_notes','notes'}
            draft={**record,**{k:v for k,v in analysis.items() if k in allowed},'human_verified':False,'verified':False,'verified_by':None,'verified_at':None,'ai_generated_draft':True,'status':'AI_GENERATED'}
            draft=ReferenceCase.model_validate(draft).model_dump(mode='json')
            if record['human_verified']:
                target=self.settings.media_dir/'drafts'/f'{reference_id}_suggested_{uuid.uuid4().hex[:8]}.json'
                atomic_json(target,draft)
                return {'record':record,'suggested_revision':draft,'protected':True,'message':'已审核记录保持不变。新的分析只生成修订建议。'}
            saved=self.repository.save('REFERENCE_CASE',draft,expected_version=expected_version,automated=True)
            atomic_json(self.settings.media_dir/'drafts'/f'{reference_id}_v{saved["version"]}.json',saved)
            return {'record':saved,'protected':False,'message':'已生成未审核草稿；mock 模式的字段需要人工填写。'}
