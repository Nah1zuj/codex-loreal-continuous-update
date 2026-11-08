"""Generate CSV research templates and editable vocabulary, without overwriting research."""
import sys
import csv
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.knowledge.vocabulary import DEFAULTS,ALIASES

TABLES={
 'LOOKS':('beauty_looks_template.csv',{'look_id':'template_look','name':'SAMPLE · 新 Look 模板','description':'请替换为研究定义','scene':'dinner','desired_impression':'polished|controlled','avoid':'too_mature|high_saturation','overall_intensity':'medium_low','overall_contrast':'medium_low','base_finish':'natural_polished','blush_intensity':'light_medium','blush_placement':'upper_cheek','blush_finish':'soft_diffused','lip_saturation':'medium_low','lip_finish':'soft_satin','eye_definition':'light_medium','routine_ids':'template_routine','source_ids':'template_source','demo_data':True}),
 'ROUTINES':('routines_template.csv',{'routine_id':'template_routine','look_id':'template_look','name':'SAMPLE · 新流程','scene':'dinner','source_ids':'template_source','demo_data':True}),
 'ROUTINE_STEPS':('routine_steps_template.csv',{'routine_id':'template_routine','step_id':'base','order':1,'name':'准备','makeup_area':'base','instruction':'先取少量常用底妆。','instruction_slow':'慢慢取少量常用底妆。','instruction_repeat':'重复：先取少量底妆。','explanation_why':'少量起步便于调整。','visual_check_required':False,'visual_task':'','success_condition':'完成准备','fallback_instruction':'你也可以跳过。'}),
 'REFERENCE_CASES':('reference_cases_template.csv',{'reference_id':'template_reference','look_id':'template_look','media_type':'image','source_file':'data/references/raw/replace-with-your-image.jpg','scene':'dinner','overall_intensity':'medium_low','blush_visible':'unknown','blush_intensity':'light_medium','blush_placement':'upper_cheek','blush_finish':'soft_diffused','lip_visible':'unknown','lip_saturation':'medium_low','lip_finish':'soft_satin','uncertainty_notes':'SAMPLE，未知字段请人工检查','source_ids':'template_source','ai_generated_draft':False,'human_verified':False,'demo_data':True}),
 'PRODUCTS':('products_template.csv',{'product_id':'template_product','brand':'SAMPLE · 虚构品牌','name':'SAMPLE · 产品模板','category':'lip','finish':'unknown','saturation':'unknown','undertone':'unknown','contexts':'dinner','look_ids':'soft_formal','claims':'','source_ids':'','source':'sample_template','source_type':'sample','verified':False,'demo_data':True}),
 'ACCESSIBILITY':('accessibility_guidance_template.csv',{'guidance_id':'template_guidance','category':'voice_instruction','principle':'one_action_at_a_time','description':'一次给一个可操作动作。','preferred_pattern':'先做一个动作，再等待确认。','avoid_pattern':'一次罗列全部动作。','example_good':'先取少量底妆。','example_bad':'把全部步骤一起完成。','source_ids':'template_source','demo_data':True}),
 'SOURCES':('sources_template.csv',{'source_id':'template_source','source_type':'team_reference','title':'SAMPLE · 模板来源，待替换','creator':'研究者','url':'','local_file':'','accessed_at':'2026-10-06','notes':'真实研究请补充可核对来源。','demo_data':True}),
}

def main():
    config=ROOT/'data/config';config.mkdir(parents=True,exist_ok=True)
    for name,values in DEFAULTS.items():
        path=config/(name+'.json')
        if not path.exists():path.write_text(json.dumps({'values':values,**({'aliases':ALIASES} if name=='scenes' else {})},ensure_ascii=False,indent=2),encoding='utf-8')
    destination=ROOT/'templates';destination.mkdir(exist_ok=True)
    for filename,row in TABLES.values():
        path=destination/filename
        if not path.exists():
            with path.open('w',newline='',encoding='utf-8-sig') as stream:
                writer=csv.DictWriter(stream,fieldnames=list(row));writer.writeheader();writer.writerow(row)
    (ROOT/'work').mkdir(exist_ok=True)
    (ROOT/'work/template_tables.json').write_text(json.dumps({name:{'headers':list(row),'values':list(row.values())} for name,(filename,row) in TABLES.items()},ensure_ascii=False),encoding='utf-8')
    print('7 CSV templates and editable controlled vocabularies are ready.')

if __name__=='__main__':main()
