"""Reviewed static demo translations. Unknown text stays explicit and intact."""
import json,re
from pathlib import Path
CATALOG=json.loads((Path(__file__).resolve().parents[3]/'data/locales/guidance.en.json').read_text(encoding='utf-8'))
def translate(text,locale):
 if locale!='en' or not isinstance(text,str) or not re.search(r'[\u3400-\u9fff]',text):return text
 if text in CATALOG:return CATALOG[text]
 result=text
 for source in sorted(CATALOG,key=len,reverse=True):result=result.replace(source,CATALOG[source])
 result=result.translate(str.maketrans({'：':': ','；':'; ','（':' (','）':')','。':'. '}))
 if re.search(r'[\u3400-\u9fff]',result):return 'Original text (translation unavailable): '+text
 return result
TEXT_FIELDS={'message','last_response','name','instruction','instruction_slow','instruction_repeat','explanation_why','reason','uncertainties','pending_coordination','reasons','texture_description','weight_drape','breathability_notes','care_notes','summary','description'}
def localize_view(value,locale,key=''):
 if isinstance(value,dict):return {k:localize_view(v,locale,k) for k,v in value.items()}
 if isinstance(value,list):return [localize_view(v,locale,key) for v in value]
 return translate(value,locale) if key in TEXT_FIELDS else value
