import json
import os
import uuid
from copy import deepcopy
from datetime import datetime,timezone
from pathlib import Path
from threading import RLock
from app.schemas.knowledge import MODELS,FILES,IDS
from app.knowledge.validation import validate_records

def now():return datetime.now(timezone.utc).isoformat()

def atomic_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
        os.replace(temporary,path)
    finally:
        if temporary.exists():temporary.unlink()

class KnowledgeRepository:
    def __init__(self,directory,history_dir=None):
        self.directory=Path(directory)
        self.history_dir=Path(history_dir or self.directory.parent/'history')
        self.lock=RLock()
    def raw(self):
        records={}
        for kind,filename in FILES.items():
            path=self.directory/filename
            raw=json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else []
            rows=raw.get('records',[]) if isinstance(raw,dict) and 'records' in raw else ([raw] if isinstance(raw,dict) else raw)
            if not isinstance(rows,list):raise ValueError(f'{filename}: records must be a list')
            records[kind]=rows
        return records
    def validate(self):return validate_records(self.raw())
    def all(self):
        report=self.validate()
        if report['errors']:raise ValueError('Knowledge validation error: '+json.dumps(report['errors'],ensure_ascii=False))
        return report['records']
    def get(self,kind,record_id):
        if kind not in MODELS:raise KeyError('Unknown knowledge type')
        result=next((r for r in self.all()[kind] if r[IDS[kind]]==record_id),None)
        if result is None:raise KeyError('Knowledge record not found')
        return result
    def save(self,kind,record,expected_version=None,reviewed=False,reviewer=None,automated=False):
        if kind not in MODELS:raise KeyError('Unknown knowledge type')
        with self.lock:
            data=self.all();incoming=deepcopy(record)
            if reviewed is True:
                if not reviewer or not reviewer.strip():raise ValueError('请填写审核者姓名。')
                incoming.update(verified=True,status='HUMAN_VERIFIED',verified_by=reviewer.strip(),verified_at=now())
                if kind=='REFERENCE_CASE':incoming['human_verified']=True
            candidate=MODELS[kind].model_validate(incoming).model_dump(mode='json')
            rid=candidate[IDS[kind]];old=next((r for r in data[kind] if r[IDS[kind]]==rid),None)
            if old:
                if expected_version!=old['version']:raise ValueError('version conflict / 此记录已更新，请重新加载。')
                if old['verified'] and (automated or reviewed is not True):raise PermissionError('Human-verified record is protected. 请通过人工审核保存修订，自动分析只能建议修改。')
            if candidate['verified'] and reviewed is not True:raise PermissionError('请勾选人工审核并填写审核者，才能保存 verified=true。')
            candidate['version']=(old['version']+1) if old else 1;candidate['updated_at']=now()
            if not candidate['verified']:
                candidate['verified_by']=None;candidate['verified_at']=None
                if kind=='REFERENCE_CASE':candidate['human_verified']=False
            data[kind]=[r for r in data[kind] if r[IDS[kind]]!=rid]+[candidate]
            report=validate_records(data)
            if report['errors']:raise ValueError(json.dumps(report['errors'],ensure_ascii=False))
            if old:self._history(kind,old)
            atomic_json(self.directory/FILES[kind],{'label':'CANONICAL KNOWLEDGE — demo_data flags preserve sample provenance','records':data[kind]})
            return candidate
    def _history(self,kind,old):
        atomic_json(self.history_dir/kind/f"{old[IDS[kind]]}_v{old['version']}_{uuid.uuid4().hex[:8]}.json",old)
    def deprecate(self,kind,record_id,expected_version):
        with self.lock:
            data=self.all();old=self.get(kind,record_id)
            if old['version']!=expected_version:raise ValueError('version conflict / 请重新加载记录。')
            candidate={**old,'status':'DEPRECATED','version':old['version']+1,'updated_at':now()}
            self._history(kind,old)
            data[kind]=[candidate if r[IDS[kind]]==record_id else r for r in data[kind]]
            atomic_json(self.directory/FILES[kind],{'records':data[kind]})
            return candidate
    def commit_import(self,records):
        """Only new drafts; no imports may overwrite existing/reviewed IDs."""
        with self.lock:
            before=self.raw();staged=self.all()
            for kind,rows in records.items():
                for r in rows:
                    if r['verified'] or r.get('human_verified'):raise PermissionError('Imports must be drafts; verify through human review')
                    if any(x[IDS[kind]]==r[IDS[kind]] for x in staged[kind]):raise ValueError('Duplicate ID conflict; import does not overwrite existing records')
                    staged[kind].append(r)
            result=validate_records(staged)
            if result['errors']:raise ValueError(json.dumps(result['errors'],ensure_ascii=False))
            changed=[]
            try:
                for kind,rows in records.items():
                    if rows:atomic_json(self.directory/FILES[kind],{'records':staged[kind]});changed.append(kind)
            except Exception:
                for kind in changed:atomic_json(self.directory/FILES[kind],{'records':before[kind]})
                raise
            return result
