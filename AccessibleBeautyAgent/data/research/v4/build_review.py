import csv, json, hashlib
from pathlib import Path
import openpyxl

ROOT=Path('D:/AccessibleBeautyAgent')
OUT=ROOT/'data/research/v4'
OUT.mkdir(parents=True,exist_ok=True)
DATE='2026-10-11'
def dump(name,data):
 (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
seed=ROOT/'_incoming/TRACE_SoftFormal_Seed_v0_1'
sources=list(csv.DictReader((seed/'evidence/source_registry.csv').open(encoding='utf-8-sig')))
verified={
'P001':('https://arxiv.org/abs/2507.03942','ABSTRACT_CHECKED','15 VI makeup users + 5 artists; contextual inquiry; tactile-first strategies and goal-aligned feedback'),
'P002':('https://arxiv.org/abs/2203.08864','ABSTRACT_CHECKED','145 YouTube videos + interviews with 12 VI people; varied practices and feedback barriers'),
'P003':('https://ualresearchonline.arts.ac.uk/id/eprint/23071/','REPOSITORY_ABSTRACT_CHECKED','Qualitative thematic analysis of BPS makeup vloggers; familiarization and iterative learning'),
'P004':('https://ualresearchonline.arts.ac.uk/id/eprint/16706/','REPOSITORY_ABSTRACT_CHECKED','Review and consumer survey; product information accessibility and familiarity'),
'P005':('https://www.microsoft.com/en-us/research/wp-content/uploads/2019/01/Guidelines-for-Human-AI-Interaction-camera-ready.pdf','ORIGINAL_ABSTRACT_CHECKED','18 general HAI guidelines evaluated through multiple rounds; not BLV makeup'),
'P006':('https://arxiv.org/abs/2405.00623','ABSTRACT_CHECKED','N=404 medical question experiment; first-person uncertainty reduced overreliance, not eliminated'),
'P008':('https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2019.00443/full','FULLTEXT_SECTION_CHECKED','14 recruited blind adults; 12 included; tactile versus auditory navigation with simulated street noise'),
'P009':('https://arxiv.org/abs/1802.08218','ABSTRACT_CHECKED','Blind-user images/questions; poor-quality and unanswerable inputs occur')}
registry=[]
for s in sources:
 if s['type']!='paper': continue
 key=s['source_id'].split('-')[-1]; v=verified.get(key)
 registry.append(dict(source_id=s['source_id'],title=s['title'],url=v[0] if v else s['doi_url'],checked_scope=v[1] if v else 'NOT_VERIFIED_THIS_RUN',summary=v[2] if v else None,local_fulltext_status='MISSING_IN_SEARCHED_PATHS',limitation='No TRACE performance validation; no full-paper claim beyond checked sections',reviewer_status='DRAFT',accessed_at=DATE))
registry.append(dict(source_id='SRC-PAPER-PSGAN',title='PSGAN: Pose and Expression Robust Spatial-Aware GAN for Customizable Makeup Transfer',url='https://arxiv.org/abs/1909.06956',checked_scope='ABSTRACT_CHECKED',summary='Image-to-image makeup synthesis, not blush recognition or efficacy validation',local_fulltext_status='MISSING_IN_SEARCHED_PATHS',reviewer_status='DRAFT',accessed_at=DATE))
dump('sources.json',registry)
rules=[]
for e in csv.DictReader((seed/'evidence/evidence_to_policy.csv').open(encoding='utf-8-sig')):
 rules.append(dict(evidence_id=e['evidence_id'],source_id=e['paper_source_id'],finding=e['source_supported_finding'],population=e['population'],method=e['study_type'],limitation='Transfer is a design inference; source checking scope in sources.json; no validated TRACE efficacy',design_implication=e['design_implication'],prompt_rule=e['anti_pattern'],prohibited_pattern='Do not universalize population preferences or claim calibrated vision',test_case=e['test_case'],transfer_level=e['transfer_level'],reviewer_status='DRAFT_REQUIRES_HUMAN_REVIEW',runtime_path='backend/app/policies/registry.py',runtime_validation='PENDING_MAIN_AGENT'))
for rule in rules:
 if rule['source_id'].endswith(('P007','P010')):
  rule.update(source_validation='NOT_VERIFIED_THIS_RUN',finding='INCOMING_CANDIDATE: '+rule['finding'],population='INCOMING_UNVERIFIED: '+rule['population'])
dump('evidence_rules.json',rules)
w=openpyxl.load_workbook(Path('C:/Users/HUAWEI/Downloads/accessibility_evidence.xlsx'),read_only=True,data_only=True)
dump('excel_inventory.json',dict(path=str(Path('C:/Users/HUAWEI/Downloads/accessibility_evidence.xlsx')),mode='READ_ONLY_DATA_ONLY',sheets=[dict(name=s.title,nonempty_rows=sum(any(v is not None for v in row) for row in s.values)) for s in w],note='Workbook is a curated screening corpus, not proof of fulltext review; source labels not promoted to HUMAN_VERIFIED'))
products=[('base','L’Oréal Paris','True Match Nude Hyaluronic Tinted Serum','natural radiant','Lightweight coverage; 1% hyaluronic acid stated by brand','https://www.lorealparisusa.com/makeup/face/true-match-nude-hyaluronic-tinted-serum-hydrates-all-in-1'),('blush','Maybelline','Cheek Heat Gel-Cream Blush','soft dewy','Water-based gel cream; buildable pigment stated by brand','https://www.maybelline.com/face-makeup/blush-and-bronzer/cheek-heat-gel-cream-blush-face-makeup'),('lip','NYX Professional Makeup','Butter Gloss Non-Sticky Lip Gloss','high shine','Sheer-to-medium coverage; non-sticky claim by brand','https://www.nyxcosmetics.com/lip/lip-gloss/butter-gloss-non-sticky-lip-gloss/NYX_089.html'),('fragrance','Lancôme','Idôle Eau de Parfum',None,'Fresh floral; rose/jasmine heart, white musk/vanilla/patchouli/cedar base stated by brand','https://www.lancome-usa.com/fragrance/fragrance-by-collection/idole/idole-eau-de-parfum/LAN387.html')]
rows=[dict(source_id=f'SRC-V4-PRODUCT-{i+1:03}',category=p[0],brand=p[1],title=p[2],region='US',shade=None,finish=p[3],official_claims=p[4],official_url=p[5],accessed_at=DATE,review_status='DRAFT',asset_rights_status='UNKNOWN',brand_portfolio_url='https://www.loreal.com/en/our-global-brands-portfolio/',independent_scientific_evidence=None) for i,p in enumerate(products)]
dump('products_candidates.json',rows)
with (OUT/'products_candidates.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
materials=[
('cotton','棉','fiber','棉是纤维；可制成挺括梭织或柔软针织，触感不能只由成分确定。','https://cottonworks.com/product-innovation/nonwovens/technical-and-performance-guide/'),
('linen','亚麻','fiber','亚麻来自亚麻植物；可有明显纹理和褶皱，但重量、混纺与整理决定具体触感。','https://allianceflaxlinenhemp.eu/en/flax-performance-and-properties'),
('wool','羊毛','fiber','羊毛纤维可制成轻薄或厚重织物；不能由羊毛名称推定一定厚热或不刺痒。','https://www.woolmark.com/industry/use-wool/product-innovations/cool-wool/'),
('silk','丝绸','fiber','丝绸纤维与缎纹不同；天然丝的成分应核对标签，照片光泽不证明是真丝。','https://silkmarkindia.com/index.php/faq/'),
('satin','缎面','weave','缎纹长浮线常形成平滑光泽表面，可能易勾丝；缎面描述不确定纤维。','https://cottonworks.com/learning-hub/weaving/basic-woven-fabric-designs/'),
('polyester','聚酯','fiber','聚酯是合成纤维类别；制造商说明其防皱特性，但具体柔软度与光泽依纱线和整理。','https://www.toray.com/aboutus/download/pdf/toray_g_dl2018.pdf'),
('viscose','粘胶','fiber','粘胶是再生纤维素纤维；不是天然丝或棉，产品性能不能照搬某厂商所有特种纤维宣传。','https://www.lenzing.com/technology-production/technologies/'),
('knit','针织','knit','针织由纱线线圈形成，通常具有结构伸展性；针织不是羊毛成分，可用多种纤维。','https://cottonworks.com/learning-hub/knitting/knit-basics/?highlight=jersey%2Bknit')]
dump('material_candidates.json',[dict(material_id=m[0],name_zh=m[1],name_en=m[0],kind=m[2],texture_description=m[3],weight_drape='以具体织物重量、织造和后整理为准',breathability_notes='透气性受结构密度、厚度、混纺和后整理影响；不作无条件排名',care_notes='以具体衣物洗护标签为准',visual_style_tags=[],source_refs=[m[4]],verification_status='DRAFT',human_verified=False,accessed_at=DATE) for m in materials])
assets=[]
for base in [seed, ROOT/'_incoming/TRACE_V4_extracted/TRACE_FullLook_Upgrade_v0_2/TRACE_FullLook_Upgrade_v0_2']:
 for p in (base/'assets').rglob('*'):
  if p.is_file() and p.suffix.lower() in ['.jpg','.jpeg','.jfif','.png']:
   assets.append(dict(asset_id=p.stem,path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),source='USER_SUPPLIED_LOCAL_BUNDLE',original_creator_if_known=None,permission_status='UNKNOWN',may_display_publicly=False,content_role='INTERNAL_REFERENCE_ONLY',AI_generated_or_advertisement='SEE_INCOMING_REVIEW_QUEUE',annotation_status='DRAFT',gold_label_eligible=False))
queue=ROOT/'_incoming/TRACE_V4_extracted/TRACE_FullLook_Upgrade_v0_2/TRACE_FullLook_Upgrade_v0_2/metadata/image_review_queue.csv'
review={r['file_path'].split('/')[-1]:r for r in csv.DictReader(queue.open(encoding='utf-8-sig'))}
for asset in assets:
 r=review.get(Path(asset['path']).name)
 if r: asset.update(content_role=r['category'],AI_generated_or_advertisement=r['synthetic_status'])
dump('assets_hash_review.json',assets)
groups={}
for a in assets:groups.setdefault(a['sha256'],[]).append(a['path'])
dump('hash_duplicates.json',dict(checked_count=len(assets),algorithm='SHA256',duplicate_groups=[dict(sha256=k,paths=v) for k,v in groups.items() if len(v)>1],note='Exact-byte comparison only; perceptual duplicates not assessed'))
print(json.dumps(dict(sources_checked=len(verified)+1,products=len(rows),materials=len(materials),assets=len(assets)),ensure_ascii=False))
