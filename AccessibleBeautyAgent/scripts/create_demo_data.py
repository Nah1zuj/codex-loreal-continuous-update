"""Generate explicitly fictional SAMPLE DATA. Do not run over a real reviewed KB."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / 'data/knowledge'

def write(name, records):
    path = out / name
    if path.exists():
        raise SystemExit(f'Refusing to overwrite {path}')
    path.write_text(json.dumps({'label': 'SAMPLE DATA — fictional hackathon content, not product claims', 'records': records}, ensure_ascii=False, indent=2), encoding='utf-8')

def main():
    out.mkdir(parents=True, exist_ok=True)
    looks = [
        {'look_id':'clean_daily','name':'Clean Daily · 清爽日常','scene':['daily'],'desired_impression':['natural','fresh'],'avoid':['heavy_makeup','high_saturation'],'base':'light_natural','blush':{'intensity':'light','placement':'upper_cheek'},'lip':{'saturation':'low','finish':'natural'},'routine_id':'clean_daily_routine'},
        {'look_id':'soft_formal','name':'Soft Formal · 柔和正式','scene':['dinner','presentation'],'desired_impression':['polished','slightly_present','controlled'],'avoid':['too_mature','high_saturation','heavy_makeup'],'base':'natural_polished','blush':{'intensity':'light_medium','placement':'upper_cheek'},'lip':{'saturation':'medium_low','finish':'soft_satin'},'routine_id':'soft_formal_routine'},
        {'look_id':'warm_social','name':'Warm Social · 温暖社交','scene':['social'],'desired_impression':['warm','approachable'],'avoid':['sharp_contrast','heavy_makeup'],'base':'natural','blush':{'intensity':'medium','placement':'cheek'},'lip':{'saturation':'medium','finish':'soft_satin'},'routine_id':'warm_social_routine'},
    ]
    for look in looks:
        look.update(source='demo_team', source_type='sample', verified=False)
    write('looks.json', looks)
    instructions = [
        ('base','准备与底妆','先把常用底妆薄薄涂在脸中央，再向外轻轻推开。','先取少量底妆。放在脸中央。用指腹慢慢向外推开。','重复：少量底妆从脸中央向外推开。','薄涂方便逐步控制用量。',False,None),
        ('blush','腮红','先把少量腮红轻拍在你左侧面颊，再在右侧重复。','先找到你左侧面颊。轻拍少量腮红。再在右側重复，暂时不要加量。','重复：左右面颊各轻拍少量腮红。','先少量试涂，方便按你的偏好调整。',True,'blush_presence'),
        ('lip','唇妆','将常用唇色轻涂在唇中央，再向两侧铺开。','先轻涂唇中央。再慢慢向左和右铺开。暂时不要叠加。','重复：从唇中央向两侧轻涂。','少量起步能帮助控制颜色存在感。',True,'lip_presence'),
        ('final','可选最终检查','如果你愿意，可以检查腮红是否在两侧可见；也可以直接跳过。','这一步可选。可以检查腮红。也可以选择跳过，完成今天的步骤。','重复：可选检查腮红，或者跳过。','检查只报告明显可见状态，不评价美丑。',False,'blush_presence'),
    ]
    keys = ['step_id','name','instruction','instruction_slow','instruction_repeat','explanation_why','visual_check_required','visual_task']
    write('routines.json', [{'routine_id':look['routine_id'],'look_id':look['look_id'],'scene':look['scene'],'steps':[dict(zip(keys,x)) for x in instructions], 'source':'demo_team','source_type':'sample','verified':False} for look in looks])
    products = []
    for i, look in enumerate(looks):
        for j, category in enumerate(['base','blush','lip','brush']):
            products.append({'product_id':f'sample_{i*4+j+1:02}','brand':'SAMPLE · 虚构演示品牌','category':category,'finish':look['lip']['finish'] if category == 'lip' else 'natural','saturation':look['lip']['saturation'] if category == 'lip' else 'low','undertone':'neutral','contexts':look['scene'],'look_ids':[look['look_id']],'claims':[],'source':'fictional_demo_catalog','source_type':'sample','verified':False})
    write('products.json', products)
    write('reference_cases.json', [{'reference_id':'soft_formal_ref_001','look_id':'soft_formal','media_type':'image','source_file':'data/references/replace-with-reviewed-image.jpg','human_verified':False,'scene':['dinner'],'overall':{'intensity':'medium_low','contrast':'medium_low'},'base':{'finish':'natural_polished'},'blush':{'visible':True,'intensity':'light_medium','placement':'upper_cheek','finish':'soft'},'lip':{'visible':True,'saturation':'medium_low','finish':'soft_satin'},'eye_definition':'minimal','notes':'SAMPLE DATA; no real media was analyzed. Replace after human review.','source':'demo_team','source_type':'sample','verified':False}])
    write('accessibility_guidance.json', [{'document_id':'guidance_one_step','scene':['daily','dinner','presentation','social'],'content':'一次给一个可执行指令。说明左右时以用户自己的左右为准。不确定就重拍，不做美丑评分。','source':'demo_team','source_type':'sample','verified':False,'tags':['voice','blush','accessibility']}])
    for path in ['data/demo','data/references','data/products','data/users','backend/app/routes','backend/app/services','frontend/src/pages','frontend/src/components','frontend/src/realtime','frontend/src/vision','frontend/src/accessibility','frontend/src/state','frontend/src/api','frontend/src/types','tests/agent','tests/rag']:
        (ROOT/path).mkdir(parents=True, exist_ok=True)
    (ROOT/'data/users/.gitkeep').touch()
    print('Created 3 looks, 3 routines, 12 fictional products and reference/guidance samples.')

if __name__ == '__main__':
    main()
