"""Version-pinned runtime rules; normative design decisions, not reviewed science."""
from pathlib import Path
import hashlib
from app.schemas.full_look import DOMAINS

POLICIES=('accessibility_policy','guidance_policy','visual_feedback_policy','full_look_planner_policy','material_description_policy','brand_copy_policy')

class PolicyRegistry:
    def __init__(self,version='v5',root=None):
        if version not in ('v4','v5'):raise ValueError('Unknown policy version')
        self.version=version
        self.root=root or Path(__file__).resolve().parents[3]/'prompts/policies'/version
        self.rules={name:self._policy_path(name).read_text(encoding='utf-8') for name in POLICIES}
    def _policy_path(self,name):
        current=self.root/(name+'.md')
        if current.exists():return current
        inherited=self.root.parent/'v4'/(name+'.md')
        if self.version=='v5' and inherited.exists():return inherited
        raise FileNotFoundError(current)
    def system(self,*names):return '\n\n'.join(self.rules[name] for name in names)
    def manifest(self):return [{'name':name,'version':self.version,'sha256':hashlib.sha256(text.encode()).hexdigest(),'review_status':'NORMATIVE_DESIGN_RULE'} for name,text in self.rules.items()]
    def validate_plan(self,p):
        if set(p.sections)!=set(DOMAINS):raise ValueError('Plan must include six optional domains')
        if p.review_status!='DEMO_CURATED':raise ValueError('Planner cannot manufacture human review')
    def guidance(self,step,style):
        fields={'normal':'instruction','expanded':'instruction_slow','repeat':'instruction_repeat','why':'explanation_why'}
        if style=='fallback':return '这一步可以暂停或跳过，也可以使用你熟悉的方法。不会补造精确位置或次数。'
        return step.get(fields[style]) or self.guidance(step,'fallback')

