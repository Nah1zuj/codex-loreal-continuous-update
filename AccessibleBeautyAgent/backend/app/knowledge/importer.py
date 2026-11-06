"""Spreadsheet/CSV import: explicit row errors, staged drafts, no overwrite."""
import csv
import io
import json
import uuid
from datetime import datetime
from pathlib import Path
from pydantic import ValidationError
from app.schemas.knowledge import MODELS,IDS
from app.knowledge.validation import validate_records
from app.knowledge.repository import now

SHEETS={'LOOKS':'LOOK','ROUTINES':'ROUTINE','ROUTINE_STEPS':'STEP','REFERENCE_CASES':'REFERENCE_CASE','PRODUCTS':'PRODUCT','ACCESSIBILITY':'ACCESSIBILITY_GUIDANCE','SOURCES':'SOURCE'}
LISTS={'scene','scenes','desired_impression','avoid','routine_ids','reference_ids','product_ids','source_ids','look_ids','contexts','claims','tags'}
BOOLS={'verified','human_verified','ai_generated_draft','demo_data','visual_check_required','visible','face_visible'}
ALIASES={'overall_intensity':'overall.intensity','overall_contrast':'overall.contrast','base_finish':'base.finish','base_coverage':'base.coverage','blush_visible':'blush.visible','blush_intensity':'blush.intensity','blush_placement':'blush.placement','blush_finish':'blush.finish','lip_visible':'lip.visible','lip_saturation':'lip.saturation','lip_finish':'lip.finish','eye_definition':'eye.definition','face_visible':'quality.face_visible','lighting':'quality.lighting','pose':'quality.pose'}

def normalize_row(raw):
    result={}
    for column,value in raw.items():
        if column is None:raise ValueError('CSV 列数超过表头，请检查引号/逗号。')
        key=ALIASES.get(str(column).strip(),str(column).strip())
        if not key or value is None or (isinstance(value,str) and not value.strip()):continue
        if isinstance(value,datetime):value=value.isoformat()
        if isinstance(value,str):
            value=value.strip()
            if value.lower() in ('null','unknown','uncertain'):value=None
            elif value.startswith(('=','+@')):raise ValueError(f'{column}: 不接受公式，请先粘贴为值。')
            elif key.split('.')[-1] in BOOLS:
                if value.lower() in ('true','yes','1','是'):value=True
                elif value.lower() in ('false','no','0','否'):value=False
                else:raise ValueError(f'{column}: 请填写 true/false。')
            elif key in LISTS:value=json.loads(value) if value.startswith('[') else [x.strip() for x in value.replace(';','|').split('|') if x.strip()]
            elif key in ('steps','overall','base','blush','lip','eye','quality'):value=json.loads(value)
        if '.' in key:
            group,field=key.split('.',1);result.setdefault(group,{})[field]=value
        else:result[key]=value
    return result

def read_rows(path,kind=None):
    if path.suffix.lower()=='.csv':
        if kind is None:
            name=path.stem.lower()
            kind=next((v for k,v in SHEETS.items() if k.lower() in name),None)
        if kind not in MODELS and kind!='STEP':raise ValueError('CSV 需要指定 --type LOOK/PRODUCT 等。')
        with path.open(encoding='utf-8-sig',newline='') as stream:
            reader=csv.DictReader(stream)
            if not reader.fieldnames or len(reader.fieldnames)!=len(set(reader.fieldnames)):raise ValueError('缺少表头或表头重复。')
            return [(kind,i,row,path.name) for i,row in enumerate(reader,2) if any(v not in (None,'') for v in row.values())]
    if path.suffix.lower()!='.xlsx':raise ValueError('只支持 .csv 或 .xlsx。')
    import zipfile
    with zipfile.ZipFile(path) as archive:
        if sum(i.file_size for i in archive.infolist())>50_000_000:raise ValueError('XLSX 解压内容过大。')
    from openpyxl import load_workbook
    book=load_workbook(path,read_only=True,data_only=False)
    rows=[]
    try:
        for sheet in book:
            kind=SHEETS.get(sheet.title.upper())
            if not kind:raise ValueError(f'{sheet.title}: 不支持的工作表，请使用模板工作表名称。')
            iterator=sheet.iter_rows(values_only=True)
            header=next(iterator,None)
            if not header:continue
            headings=[str(x).strip() if x is not None else '' for x in header]
            if len([x for x in headings if x])!=len(set(x for x in headings if x)):raise ValueError(f'{sheet.title}: 表头重复。')
            for i,values in enumerate(iterator,2):
                if i>10001:raise ValueError('一次导入最多 10000 行。')
                if any(v is not None and not h for h,v in zip(headings,values)):raise ValueError(f'{sheet.title} row {i}: 有数据的列缺少表头。')
                if any(x is not None for x in values):rows.append((kind,i,{h:v for h,v in zip(headings,values) if h},sheet.title))
        if not rows:raise ValueError('没有找到支持的工作表或非空记录。')
        return rows
    finally:book.close()

def import_file(path,repository,kind=None,commit=False):
    rows=read_rows(Path(path),kind);existing=repository.all();items=[];errors=[];warnings=[]
    seen={k:{r[IDS[k]] for r in v} for k,v in existing.items()}
    def error(entry,field,message):errors.append({'type':entry[0],'row':entry[1],'sheet':entry[3],'field':field,'message':message})
    steps={};step_entries={}
    for entry in rows:
        if entry[0]!='STEP':continue
        try:
            value=normalize_row(entry[2]);rid=value.pop('routine_id',None)
            if not rid:raise ValueError('routine_id: 步骤需要关联一个流程。')
            from app.schemas.knowledge import RoutineStep
            step=RoutineStep.model_validate(value).model_dump(mode='json')
            steps.setdefault(rid,[]).append(step);step_entries.setdefault(rid,[]).append(entry)
        except (ValueError,TypeError) as exc:error(entry,'routine_id/step',str(exc))
    for entry in rows:
        k,row,raw,sheet=entry
        if k=='STEP':continue
        try:
            value=normalize_row(raw)
            if k=='ROUTINE' and value.get('routine_id') in steps:value['steps']=steps[value['routine_id']]
            if value.get('verified') or value.get('human_verified'):warnings.append({'row':row,'sheet':sheet,'field':'verified','message':'导入只创建草稿；请在后台进行人工审核。'})
            value.update(verified=False,status='DRAFT',verified_by=None,verified_at=None,version=1,updated_at=now())
            if k=='REFERENCE_CASE':value['human_verified']=False
            normalized=MODELS[k].model_validate(value).model_dump(mode='json');rid=normalized[IDS[k]]
            if rid in seen[k]:error(entry,IDS[k],f'Duplicate ID / 编号已存在：{rid}。导入不会覆盖已有记录。');continue
            seen[k].add(rid);items.append((entry,normalized))
        except ValidationError as exc:
            for err in exc.errors():error(entry,'.'.join(map(str,err['loc'])),('必填字段缺失' if err['type']=='missing' else err['msg']))
        except (ValueError,TypeError) as exc:error(entry,'row',str(exc))
    # Reject dependent rows until every accepted row has valid references.
    while items:
        staged={k:list(v) for k,v in existing.items()};origins={}
        for entry,r in items:
            k=entry[0];origins[(k,len(staged[k])+2)]=entry;staged[k].append(r)
        validation=validate_records(staged)
        bad=set()
        for e in validation['errors']:
            entry=origins.get((e['type'],e['row']))
            if entry:error(entry,e['field'],e['message']);bad.add((entry[0],entry[1],entry[3]))
        if not bad:
            for w in validation['warnings']:
                entry=origins.get((w['type'],w['row']))
                if entry:warnings.append({**w,'row':entry[1],'sheet':entry[3]})
            break
        items=[(e,r) for e,r in items if (e[0],e[1],e[3]) not in bad]
    accepted_routines={r['routine_id'] for e,r in items if e[0]=='ROUTINE'}
    for rid,entries in step_entries.items():
        if rid not in accepted_routines:
            for entry in entries:error(entry,'routine_id','关联流程未成功导入；步骤没有丢弃到其他流程。')
    rejected={(e['type'],e['row'],e['sheet']) for e in errors}
    staged={k:[] for k in MODELS}
    for entry,r in items:staged[entry[0]].append(r)
    if commit and any(staged.values()):repository.commit_import(staged)
    accepted=len(items)+sum(len(entries) for rid,entries in step_entries.items() if rid in accepted_routines)
    return {'total_rows':len(rows),'accepted':accepted,'warnings':len(warnings),'rejected':len(rejected),'errors':errors,'warning_details':warnings,'records':staged,'committed':commit,'report_id':'import_'+uuid.uuid4().hex,'timestamp':now()}
