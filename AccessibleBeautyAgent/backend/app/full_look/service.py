"""One planner attached to the existing Agent/session, with scoped user edits."""
import uuid
from app.schemas.full_look import DOMAINS, FullLook, LookSection, Suggestion
from app.schemas.models import Stage
from app.full_look.materials import MaterialService

LABELS={'skincare':'护肤与妆前','makeup':'妆容','hair':'发型','outfit':'穿搭','accessories':'配饰','fragrance':'香氛'}

class FullLookService:
    def __init__(self,agent):self.agent=agent;self.materials=MaterialService()
    def editable(self,s):
        if s.stage==Stage.COMPLETE:raise ValueError('会话已结束，请开始新会话。')
        if s.stage in (Stage.CAMERA_CONSENT,Stage.VISION_GATE,Stage.VISION_CHECK):raise ValueError('请先结束本次相机请求，再调整造型。')
        if s.stage==Stage.MEMORY_CONSENT:raise ValueError('请先处理待确认的记忆。')
    def get(self,s):
        if s.todays_look is None:raise KeyError('今天还没有造型计划。')
        return s.todays_look
    def suggestion(self,key,name,reason,en='',user=False):
        return Suggestion(id=key,display_name_zh=name,display_name_en=en,reason=reason,user_override=user)
    def plan(self,s):
        self.editable(s)
        if s.todays_look is not None:return s.todays_look
        if not s.selected_look and not s.makeup_plan:raise ValueError('请先表达场景并选择妆容方向。')
        rows={
            'skincare':('保留你已知可耐受的基础妆前准备','可省略；不诊断皮肤，也不推断过敏安全。','Your familiar prep'),
            'makeup':('Soft Formal · 柔和正式','这是场景演示方向；你可以只做熟悉的步骤。','Soft Formal'),
            'hair':('低马尾、自然半扎，或保留原有发型','可选方向，先由你决定是否方便扎发。','Keep your style or a simple tie'),
            'outfit':('米白与浅咖等低冲突配色方向','只从你确认拥有的衣物选择；不假设衣橱或天气。','Ivory and light brown direction'),
            'accessories':('可选的简洁配件，也可以不佩戴','不假设你戴耳饰，也不承诺金属低敏。','Optional simple accessories'),
            'fragrance':('可选淡花香或花木调方向，也可以无香','属于主观风格方向；没有具体产品或气味观察。','Optional floral/woody direction'),
        }
        sections={key:LookSection(suggestions=[self.suggestion(key,*row)]) for key,row in rows.items()}
        sections['makeup'].look_id=s.selected_look;sections['makeup'].routine_id=s.routine_id
        # Do not relabel a different selected look as Soft Formal.
        if s.selected_look and s.selected_look!='soft_formal':sections['makeup'].suggestions=[self.suggestion('makeup',self.agent.store.look_map[s.selected_look]['name'],'沿用你当前选择的妆容方向。')]
        elif not s.selected_look:
            # Reuse the actual coaching plan. Do not select a legacy preset or
            # reset progress to satisfy the visual presentation.
            sections['makeup'].suggestions=[self.suggestion('coaching_makeup','本次上妆计划','沿用当前步骤：'+'、'.join(step.title for step in s.makeup_plan.steps)+'。美没有统一的定义，按你喜欢的方式表达就好。','Your current makeup plan')]
        s.todays_look=FullLook(plan_id='look_'+uuid.uuid4().hex,session_id=s.session_id,scene=s.scene or 'unspecified',desired_impression=s.desired_impression,sections=sections,uncertainties=['人工策划演示草稿，尚未作为真实商品推荐审核。','天气、衣橱、发长、皮肤与佩戴偏好未知；可以澄清或修改。'])
        self.agent.policies.validate_plan(s.todays_look)
        return s.todays_look
    def version(self,p,expected):
        if expected is not None and expected!=p.version:raise ValueError('方案版本已更新，请刷新后再修改。')
    def revise(self,s,request):
        self.editable(s);p=self.get(s);self.version(p,request.expected_version)
        text=request.user_request.strip();t=text.lower();changes={};reasons=[]
        def put(key,name,reason,materials=None,skip=False):
            changes[key]=LookSection(state='skipped' if skip else 'proposed',suggestions=[] if skip else [self.suggestion(key+'_'+str(p.version+1),name,reason,user=True)],materials=materials or [])
            if materials:
                changes[key].suggestions[0].source_refs=list(dict.fromkeys(url for mid in materials for url in self.materials.by_id[mid]['source_refs']))
            reasons.append(reason)
        if any(x in t for x in ('只要妆容','只做妆容','makeup only')):
            for key in DOMAINS:
                if key!='makeup':put(key,'','按你的选择，暂不安排这个领域。',skip=True)
        else:
            if any(x in t for x in ('不扎头发','不扎发','keep my hair','不要扎','保留发型')):put('hair','保留你原有的发型','你选择不扎头发；其它已确认项保留。')
            elif any(x in t for x in ('发型','头发','hair')):put('hair',text,'记录你明确提出的发型方向，未推断发长或可行性。')
            if any(x in t for x in ('黑色连衣裙','black dress')):
                put('outfit','你选择的黑色连衣裙','已固定你确认的衣物；其它领域不自动改变。')
            elif any(x in t for x in ('棉质衬衫','棉衬衫','cotton shirt')) and not any(x in t for x in ('看着像','看起来像','照片','可能','不知道','不确定','不是','没有','不穿','不想','maybe','looks like','not ','no ','unsure','photo')):put('outfit','你确认已有的棉质衬衫','成分由你的明确陈述提供，不由照片推断。',['cotton'])
            elif any(x in t for x in ('透气','breathable','不那么有光泽','比缎面更日常')):
                put('outfit','比较棉与亚麻的具体织物，再由你选择','透气和光泽受结构、厚度及后整理影响；天气未知，不编造温度。',['cotton','linen'])
            elif any(x in t for x in ('衣服','穿搭','outfit','衬衫','裙')):put('outfit',text,'记录你选择的穿搭；缺少的成分信息保持未知。')
            if any(x in t for x in ('不要耳环','不戴耳','不带耳','不想戴耳','不想带耳','no earrings','不佩戴饰品')):put('accessories','','按你的选择跳过耳饰/配饰。',skip=True)
            elif any(x in t for x in ('饰品','配饰','项链','accessories')):put('accessories',text,'保留你提出的佩戴选择，未假设材质安全。')
            if any(x in t for x in ('不想喷香水','不喷香水','不想用香水','不想喷香','no fragrance','无香','不用香水')):put('fragrance','','按你的选择跳过香氛，不再推荐。',skip=True)
            elif any(x in t for x in ('不喜欢甜香','不要甜香','not sweet')):put('fragrance','避免甜香；可选你熟悉的木质方向或无香','只调整本次香氛方向；没有写入长期记忆。')
            elif any(x in t for x in ('香水','香氛','fragrance')):put('fragrance',text,'仅记录你表达的气味方向，没有摄像头闻味或疗效推断。')
        for key,value in request.constraints.items():
            if len(value)>2000:raise ValueError('单个约束不能超过2000字。')
            put(key,value,'你明确指定的局部约束，优先于演示建议。')
        if not changes and request.target_sections:
            for key in request.target_sections:put(key,text,'你明确指定的局部选择；其它领域保留。')
        if request.target_sections and not set(changes).issubset(request.target_sections):raise ValueError('修改范围与识别的领域不一致，请确认目标领域。')
        for key,section in changes.items():
            if key=='makeup':
                section.look_id=s.selected_look;section.routine_id=s.routine_id
                if section.suggestions:section.suggestions[0].reason+=' 妆容意愿已记录；现有步骤保持原方案，具体步骤调整需要另行确认。'
            p.sections[key]=section
            if key in p.user_confirmed_sections:p.user_confirmed_sections.remove(key)
        if changes:
            p.version+=1
            p.pending_coordination=['你愿意再讨论配饰或唇色与黑裙的协调吗？未获同意前不会修改其它项。'] if '黑色连衣裙' in t or 'black dress' in t else []
        return {'plan':p.model_dump(),'changed_sections':list(changes),'unchanged_sections':[k for k in DOMAINS if k not in changes],'reasons':reasons or ['没有识别到要修改的领域，请说明发型、穿搭、配饰或香氛。'],'version':p.version}
    def confirm(self,s,request):
        self.editable(s);p=self.get(s);self.version(p,request.expected_version)
        for key in dict.fromkeys(request.sections):
            p.sections[key].state='confirmed' if request.decision=='confirm' else 'skipped'
            if request.decision=='confirm' and key not in p.user_confirmed_sections:p.user_confirmed_sections.append(key)
            if request.decision=='skip' and key in p.user_confirmed_sections:p.user_confirmed_sections.remove(key)
        p.version+=1;return p
    def summary(self,s,section=None):
        p=self.get(s);keys=[section] if section else DOMAINS
        return '\n'.join([f'今日造型 v{p.version}：场景演示草稿，由你决定。']+[LABELS[k]+'：'+('按你的选择跳过。' if p.sections[k].state=='skipped' else '；'.join(x.display_name_zh for x in p.sections[k].suggestions)) for k in keys])
    def memory_candidate(self,s,feedback):
        self.editable(s);p=self.get(s)
        candidate=self.agent.propose_memory_update(feedback);candidate['context']=s.scene or 'unspecified'
        candidate['material_preferences']=list(dict.fromkeys(p.sections['outfit'].materials))
        candidate['domain_preferences']={k:[x.display_name_zh for x in sec.suggestions if x.user_override] for k,sec in p.sections.items() if any(x.user_override for x in sec.suggestions)}
        s.memory_candidate=candidate;self.agent.sessions.transition(s,Stage.MEMORY_CONSENT)
        return candidate

