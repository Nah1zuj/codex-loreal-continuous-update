from pydantic import ValidationError
from app.schemas.knowledge import MODELS,IDS
from app.knowledge.vocabulary import Vocabulary

def validate_records(raw,vocabulary=None):
    """Return schema/cross-link ERRORs plus non-fatal vocabulary/provenance WARNINGs."""
    vocabulary=vocabulary or Vocabulary()
    errors=[];warnings=[];normalized={kind:[] for kind in MODELS}
    def issue(target,kind,row,field,message):target.append({'type':kind,'row':row,'field':field,'message':message})
    for kind,records in raw.items():
        if kind not in MODELS:continue
        seen=set()
        for i,record in enumerate(records,2):
            try:
                value=MODELS[kind].model_validate(record).model_dump(mode='json')
                rid=value[IDS[kind]]
                if rid in seen:issue(errors,kind,i,IDS[kind],f'Duplicate ID / 重复编号：{rid}')
                seen.add(rid);normalized[kind].append(value)
            except ValidationError as exc:
                for error in exc.errors():issue(errors,kind,i,'.'.join(map(str,error['loc'])),error['msg'])
    ids={kind:{r[IDS[kind]] for r in rows} for kind,rows in normalized.items()}
    def linked(kind,row,field,values,target):
        for value in values:
            if value not in ids[target]:issue(errors,kind,row,field,f'Unknown {target.lower()} reference / 找不到关联编号：{value}')
    for kind,rows in normalized.items():
        for i,r in enumerate(rows,2):
            linked(kind,i,'source_ids',r.get('source_ids',[]),'SOURCE')
            if kind!='SOURCE' and not r.get('source_ids') and r.get('source')=='unknown':issue(warnings,kind,i,'source_ids','来源尚未填写，请在审核前补充。')
            if kind=='SOURCE' and not r.get('url') and not r.get('local_file'):issue(warnings,kind,i,'url/local_file','来源尚无 URL 或文件，请在研究后补充。')
            if kind in ('ROUTINE','REFERENCE_CASE'):linked(kind,i,'look_id',[r['look_id']],'LOOK')
            if kind=='PRODUCT':linked(kind,i,'look_ids',r['look_ids'],'LOOK')
            if kind=='LOOK':
                for field,target in [('routine_ids','ROUTINE'),('reference_ids','REFERENCE_CASE'),('product_ids','PRODUCT')]:linked(kind,i,field,r[field],target)
                if not r['routine_ids']:issue(warnings,kind,i,'routine_ids','Look 还没有关联步骤；Agent 不会启动缺失的流程。')
            checks=[('scene','scenes',r.get('scene',r.get('contexts',[]))),('desired_impression','impressions',r.get('desired_impression',[]))]
            for area in ('overall','base','blush','lip','eye'):
                attrs=r.get(area,{})
                for field,vocab in [('intensity','intensity_levels'),('contrast','intensity_levels'),('definition','intensity_levels'),('finish','finishes'),('saturation','saturation_levels'),('placement','placements')]:
                    if isinstance(attrs,dict) and attrs.get(field):checks.append((area+'.'+field,vocab,[attrs[field]]))
            if kind=='PRODUCT':
                checks.extend([('category','makeup_areas',[r['category']]),('finish','finishes',[r['finish']] if r['finish'] else []),('saturation','saturation_levels',[r['saturation']] if r['saturation'] else [])])
            for field,vocab,values in checks:
                for value in values:
                    if value not in vocabulary.values[vocab]:issue(warnings,kind,i,field,f'词表尚无“{value}”；请确认拼写或在 data/config/{vocab}.json 添加。')
    # A Look must not claim a routine belonging to another Look.
    routines={r['routine_id']:r for r in normalized['ROUTINE']}
    for i,look in enumerate(normalized['LOOK'],2):
        for rid in look['routine_ids']:
            if rid in routines and routines[rid]['look_id']!=look['look_id']:issue(errors,'LOOK',i,'routine_ids',f'Routine {rid} belongs to a different look')
    return {'status':'ERROR' if errors else ('WARNING' if warnings else 'PASS'),'errors':errors,'warnings':warnings,'records':normalized}
