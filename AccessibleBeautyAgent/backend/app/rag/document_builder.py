"""Canonical records -> readable, sourced parent/child documents."""
from app.schemas.knowledge import KnowledgeDocument
from app.knowledge.curriculum import lesson_sources

def details(values):return '；'.join(f'{key}: {value}' for key,value in values.items() if value is not None and value!='')

def build_documents(store):
    docs=[];source_map={s['source_id']:s for s in store.sources}
    def add(doc_id,kind,title,content,row,parent=None,area=None,look_id=None,subtype=None):
        sources=[source_map[sid] for sid in row.get('source_ids',[]) if sid in source_map]
        source='; '.join(s.get('url') or s['title'] for s in sources) or row.get('source','unknown')
        metadata={'document_id':doc_id,'document_type':kind,'subtype':subtype or kind,'look_id':look_id or row.get('look_id'),'scene':row.get('scene',row.get('contexts',[])),'makeup_area':area,'source_type':row.get('source_type','other'),'source':source,'source_ids':row.get('source_ids',[]),'verified':row.get('verified',False),'demo_data':row.get('demo_data',False),'status':row.get('status','DRAFT'),'parent_id':parent,'tags':row.get('tags',[]),'version':row.get('version',1)}
        metadata.update(verified_by=row.get('verified_by'), verified_at=row.get('verified_at'))
        if subtype=='makeup_lesson':
            metadata['language']=next((tag for tag in row['tags'] if tag in ('zh-CN','en')),None)
            metadata['source_rights_confirmed']=bool(lesson_sources(row,source_map))
            metadata['sources']=[{key:s[key] for key in ('source_id','title','version','use_permission','use_basis')} for s in sources]
        docs.append(KnowledgeDocument(document_id=doc_id,document_type=kind,title=title,content=title+'\n'+content,source=source,metadata=metadata).model_dump())
    for look in store.looks:
        lid=look['look_id'];name=look['name']
        content=f"适用场景 / Scenes: {', '.join(look['scene'])}。\n{look['description']}\n期望印象: {', '.join(look['desired_impression'])}。避免: {', '.join(look['avoid'])}。\n整体: {details(look['overall'])}"
        add(lid,'LOOK',name,content,look)
        for area in ('base','blush','lip','eye'):
            if area=='eye' and not any(look[area].values()):continue
            add(f'{lid}:{area}','LOOK',f'{name} — {area}',f"场景: {', '.join(look['scene'])}。{details(look[area])}",look,lid,area,subtype='LOOK_COMPONENT')
    for routine in store.routines:
        rid=routine['routine_id'];look=store.look_map[routine['look_id']];effective={**routine,'scene':routine['scene'] or look['scene']}
        add(rid,'ROUTINE',routine['name'] or look['name']+' — routine','流程顺序: '+' → '.join(s['name'] for s in routine['steps']),effective,routine['look_id'])
        for step in routine['steps']:
            content=f"步骤 {step['order']}: {step['instruction']}\n慢速: {step['instruction_slow']}\n原因: {step['explanation_why']}\n成功条件: {step['success_condition']}\n无法确认时: {step['fallback_instruction']}"
            add(f"{rid}:{step['step_id']}",'ROUTINE',look['name']+' — '+step['name'],content,effective,rid,step['makeup_area'] or step['step_id'],subtype='ROUTINE_STEP')
    for row in store.references:
        look=store.look_map[row['look_id']]
        content='\n'.join([f"场景: {', '.join(row['scene'])}",*[f'{area}: {details(row[area])}' for area in ('overall','base','blush','lip','eye')],f"记录说明: {row['notes']}",f"不确定性: {row['uncertainty_notes']}",f"审核备注: {row['review_notes']}"])
        add(row['reference_id'],'REFERENCE_CASE',look['name']+' — Reference '+row['reference_id'],content,row,row['look_id'])
    for row in store.products:
        content=f"品牌: {row['brand']}。类别: {row['category']}。\n{details({k:row[k] for k in ('finish','saturation','undertone')})}\n官方声明: {'; '.join(row['claims']) if row['claims'] else '信息不可用 / unknown'}"
        for lid in row['look_ids'] or [None]:add(f"{row['product_id']}:{lid}" if lid else row['product_id'],'PRODUCT',row['name'] or row['brand']+' '+row['category'],content,row,lid,row['category'],lid)
    for row in store.guidance:
        teaching=row.get('teaching')
        content=row['content']+'\n推荐: '+row['preferred_pattern']+'\n避免: '+row['avoid_pattern']+'\n例子: '+row['example_good']
        if teaching:
            content+='\n'+'\n'.join([*teaching['requiredProducts'], *teaching['instructions'], *teaching['accessibilityInstructions']])
        add(row['guidance_id'],'ACCESSIBILITY_GUIDANCE',row['principle'] or row['category'],content,row,
            area=next((tag for tag in row['tags'] if tag not in ('zh-CN','en','original_draft')),None) if teaching else None,
            subtype=row['category'] if teaching else None)
    ids={d['document_id'] for d in docs}
    if len(ids)!=len(docs):raise ValueError('Duplicate RAG document ID')
    if any(d['metadata']['parent_id'] and d['metadata']['parent_id'] not in ids for d in docs):raise ValueError('Broken RAG parent reference')
    return docs
