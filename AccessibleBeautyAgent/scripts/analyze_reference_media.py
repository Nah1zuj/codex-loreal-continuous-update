"""Batch/local image drafts using the same admin/reference adapter. Human review required."""
import sys
import argparse
import base64
import uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.config import Settings
from app.knowledge.admin_service import KnowledgeAdminService
from app.knowledge.repository import atomic_json

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('image',type=Path,nargs='?');p.add_argument('--input',type=Path)
    p.add_argument('--look-id',required=True);p.add_argument('--reference-id')
    p.add_argument('--provider',choices=['mock','deepseek','qwen'],default='mock');p.add_argument('--output',type=Path)
    a=p.parse_args();source=a.input or a.image
    if source is None:p.error('请指定 image 或 --input 文件夹。')
    files=sorted(x for x in source.iterdir() if x.suffix.lower() in ('.jpg','.jpeg','.png','.webp')) if source.is_dir() else [source]
    if a.reference_id and len(files)!=1:p.error('--reference-id 只用于单个图片。')
    if a.output and not a.output.resolve().is_relative_to(ROOT.resolve()):p.error('Output must be inside the project directory')
    settings=Settings(reference_provider=a.provider);service=KnowledgeAdminService(None,settings)
    processed=[];errors=[]
    for path in files:
        try:
            if a.output and a.output.exists():raise ValueError('输出已存在，不覆盖。')
            if a.reference_id:
                try:record=service.repository.get('REFERENCE_CASE',a.reference_id)
                except KeyError:record=service.upload(path.name,a.look_id,base64.b64encode(path.read_bytes()).decode(),reference_id=a.reference_id)
            else:record=service.upload(path.name,a.look_id,base64.b64encode(path.read_bytes()).decode())
            result=service.analyze(record['reference_id'],record['version'])
            draft=result.get('suggested_revision',result['record'])
            if a.output:atomic_json(a.output,draft)
            processed.append({'file':str(path),'reference_id':record['reference_id'],'human_verified':False,'protected_existing':result['protected']})
        except Exception as exc:errors.append({'file':str(path),'message':str(exc)})
    report={'processed':processed,'errors':errors,'provider':a.provider,'human_review_required':True}
    destination=settings.reports_dir/('analysis_'+uuid.uuid4().hex+'.json');atomic_json(destination,report)
    print(f'Processed={len(processed)} errors={len(errors)}; report={destination}')
    if errors:raise SystemExit(1)

if __name__=='__main__':main()
