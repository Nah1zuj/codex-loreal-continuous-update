"""Durable, owner-scoped coaching. No transcript, images or consent persisted here."""
import json,re,time,uuid
from datetime import datetime
from pydantic import ValidationError
from app.schemas.makeup import MakeupPlan,MakeupStep,PlanNeeds,PlanProposal,Lesson
from app.schemas.models import Stage
from app.agent.coaching_intents import coaching_intent

TEMPLATES={
    'natural':('自然日常','Natural everyday',['prep','foundation','blush','lips','finish']),
    'warm':('柔和暖调','Soft warm',['prep','foundation','eyes','blush','lips','finish']),
    'professional':('简约通勤','Minimal professional',['prep','foundation','concealer','brows','lips','finish']),
    'evening':('柔和晚间','Gentle evening',['prep','foundation','eyes','blush','lips','finish']),
    'beginner':('简单初学','Simple beginner',['prep','blush','lips','finish']),
}

class CoachingController:
    def __init__(self,agent):self.agent=agent
    def knowledge(self,locale,reviewed_only=True):
        rows=[r for r in self.agent.store.guidance if r.get('category')=='makeup_lesson' and locale in r.get('tags',[]) and r.get('status') not in ('REJECTED','DEPRECATED')]
        if reviewed_only:rows=[r for r in rows if r.get('verified') and r.get('status')=='HUMAN_VERIFIED' and r.get('verified_by') and r.get('verified_at') and not r.get('demo_data')]
        return rows
    def create(self,s,needs,candidate=None):
        needs=PlanNeeds.model_validate(needs)
        if s.makeup_plan and s.makeup_plan.status=='active':raise ValueError('Finish the active plan before replacing it')
        rows=self.knowledge(s.locale)
        reviewed=bool(rows)
        if not rows:
            if not self.agent.settings.developer_mode:raise ValueError('Expert-reviewed makeup lessons are not available')
            rows=self.knowledge(s.locale,False)
        topics=TEMPLATES[needs.style][2]
        if needs.complexity=='standard' and needs.minutes>=30:topics=['prep','primer','foundation','concealer','brows','eyes','blush','lips','finish']
        by_id={r['guidance_id']:r for r in rows}
        selected=[next((r for r in rows if topic in r['tags']),None) for topic in topics]
        fallback=False
        if candidate is not None:
            try:
                proposal=PlanProposal.model_validate(candidate)
                if len(set(proposal.lesson_ids))!=len(proposal.lesson_ids) or any(k not in by_id for k in proposal.lesson_ids):raise ValueError('Unknown lessons')
                proposed=[by_id[k] for k in proposal.lesson_ids]
                # A complete routine must include safe preparation and finishing.
                if 'prep' not in proposed[0]['tags'] or 'finish' not in proposed[-1]['tags']:raise ValueError('Incomplete plan')
                selected=proposed
            except (ValidationError,ValueError):fallback=True
        if any(row is None for row in selected):raise ValueError('Curriculum coverage missing; active state unchanged')
        steps=[MakeupStep(id=r['guidance_id'],order=i+1,title=r['principle'],source_id=r['guidance_id'],review_status=r['status'],**Lesson.model_validate(r['teaching']).model_dump()) for i,r in enumerate(selected)]
        plan=MakeupPlan(id=str(uuid.uuid4()),userId=s.user_id,sessionId=s.session_id,name=TEMPLATES[needs.style][0 if s.locale=='zh-CN' else 1],occasion=needs.occasion,styleDescription=needs.aesthetic or needs.style,estimatedMinutes=needs.minutes,needs=needs,steps=steps,date=datetime.now().astimezone().date().isoformat(),generation_status='fallback' if fallback else 'grounded',knowledge_status='reviewed' if reviewed else 'draft')
        with self.agent.sessions.lock:
            with self.agent.memory.connect() as db:
                db.execute('INSERT OR REPLACE INTO makeup_sessions VALUES (?,?,?,?,?)',(s.session_id,s.user_id,s.locale,plan.model_dump_json(),time.time()))
                db.execute('DELETE FROM makeup_events WHERE session_id=?',(s.session_id,))
            s.makeup_plan=plan;self.sync(s)
        return plan
    def sync(self,s):
        p=s.makeup_plan
        if not p:return
        s.routine_step=p.active_index;s.routine_total_steps=len(p.steps);s.routine_started=p.status!='draft'
        s.stage=Stage.FEEDBACK if p.status=='completed' else Stage.GUIDE if p.status=='active' else Stage.LOOK_SELECTED
        s.scene=p.occasion
    def current(self,s):
        p=s.makeup_plan
        if not p or p.status=='draft' or p.status=='completed':return None
        step=p.steps[p.active_index]
        localized_id=re.sub(r'_(zh|en)$','_zh' if s.locale=='zh-CN' else '_en',step.source_id)
        row=next((r for r in self.agent.store.guidance if r['guidance_id']==localized_id and r.get('teaching')),None)
        lesson=Lesson.model_validate(row['teaching']) if row else step
        prefix=('美没有统一的定义，按你喜欢的方式表达就好。' if s.locale=='zh-CN' else 'Beauty has no single definition. Express yourself in your own way. ') if p.knowledge_status=='draft' else ''
        return {'step_id':step.id,'name':row['principle'] if row else step.title,'instruction':prefix+' '.join(lesson.preparation+lesson.instructions+lesson.accessibilityInstructions),'instruction_repeat':prefix+' '.join(lesson.instructions),'instruction_slow':prefix+' '.join(lesson.instructions+lesson.commonMistakes),'explanation_why':lesson.purpose,'visual_check_required':False,'visual_task':step.optionalVisualCheck,'status':step.status,'source_id':step.source_id,'review_status':step.review_status}
    def act(self,s,intent,event_id=None,expected_step_id=None):
        event_id=event_id or str(uuid.uuid4())
        with self.agent.sessions.lock:
            with self.agent.memory.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                row=db.execute('SELECT payload FROM makeup_sessions WHERE session_id=? AND user_id=?',(s.session_id,s.user_id)).fetchone()
                if not row:raise ValueError('No plan for this owner')
                p=MakeupPlan.model_validate_json(row[0])
                if db.execute('SELECT 1 FROM makeup_events WHERE session_id=? AND event_id=?',(s.session_id,event_id)).fetchone():
                    s.makeup_plan=p;self.sync(s);return {'duplicate':True,'plan':p.model_dump(),'step':self.current(s)}
                if expected_step_id and expected_step_id!=p.steps[p.active_index].id:raise ValueError('Step changed; read current step before retrying')
                if intent=='start':
                    if p.status=='completed':raise ValueError('Session is complete')
                    p.status='active';p.workflow='WAITING_FOR_USER'
                    if p.steps[p.active_index].status=='pending':p.steps[p.active_index].status='active'
                elif intent=='pause':
                    if p.status!='active':raise ValueError('No active session to pause')
                    p.workflow='PAUSED'
                elif intent=='resume':
                    if p.workflow!='PAUSED':raise ValueError('Session is not paused')
                    p.workflow='WAITING_FOR_USER'
                elif intent in ('advance','complete','previous','blush','skip'):
                    if p.status!='active' or p.workflow=='PAUSED':raise ValueError('Start or resume the session first')
                    if intent in ('advance','complete'):p.steps[p.active_index].status='completed'
                    if intent=='skip' and p.steps[p.active_index].status!='completed':p.steps[p.active_index].status='skipped'
                    if intent=='previous':p.active_index=max(0,p.active_index-1)
                    elif intent=='blush':
                        index=next((i for i,step in enumerate(p.steps) if step.optionalVisualCheck=='blush_presence'),None)
                        if index is None:raise ValueError('No blush step in this plan')
                        p.active_index=index
                    elif intent in ('advance','skip'):
                        if p.active_index==len(p.steps)-1:p.status='completed';p.workflow='SESSION_COMPLETE'
                        else:p.active_index+=1
                    if p.status=='active' and p.steps[p.active_index].status=='pending':p.steps[p.active_index].status='active'
                elif intent=='finish':
                    # User ending early does not claim unperformed steps are completed.
                    if p.status=='draft':raise ValueError('Start the plan before finishing')
                    p.status='completed';p.workflow='SESSION_COMPLETE'
                elif intent not in ('repeat','explain','visual'):raise ValueError('Unknown action')
                p.revision+=1
                p.summary_presented=False
                db.execute('UPDATE makeup_sessions SET payload=?,locale=?,updated_at=? WHERE session_id=? AND user_id=?',(p.model_dump_json(),s.locale,time.time(),s.session_id,s.user_id))
                db.execute('INSERT INTO makeup_events VALUES (?,?,?)',(s.session_id,event_id,intent))
            s.makeup_plan=p;self.sync(s)
            if p.status=='completed' and getattr(self.agent,'recollection',None):self.agent.recollection.remember(s)
            if intent=='visual':s.visual_state=None;s.confidence=0
            return {'plan':p.model_dump(),'step':self.current(s),'visual_request':intent=='visual','frame_obtained':False if intent=='visual' else None}
    def summary(self,s):
        p=s.makeup_plan
        if not p or p.status!='completed':raise ValueError('Finish the session before summarizing')
        return {'chosen_look':p.name,'date':p.date,'completed_steps':[step.title for step in p.steps if step.status=='completed'],'techniques_practiced':[' '.join(step.instructions) for step in p.steps if step.status=='completed'],'preferences':self.agent.memory.profile(s.user_id)['profile'],'feelings':None,'observations':s.visual_state if s.visual_state and not s.visual_state.get('simulated',False) else None,'future_advice':'下次可重复尚不熟悉的步骤。' if s.locale=='zh-CN' else 'Practice an unfamiliar step next time.','knowledge_status':p.knowledge_status,'requires_confirmation':True}
    def save(self,s,user_text):
        if coaching_intent(user_text)!='save':raise PermissionError('Explicit journal confirmation required')
        if not s.makeup_plan or not s.makeup_plan.summary_presented:raise PermissionError('Read the completed session summary before saving')
        summary=self.summary(s)
        with self.agent.sessions.lock:
            with self.agent.memory.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                row=db.execute('SELECT payload FROM makeup_sessions WHERE session_id=? AND user_id=?',(s.session_id,s.user_id)).fetchone()
                if not row:raise PermissionError('Plan owner mismatch')
                p=MakeupPlan.model_validate_json(row[0])
                if p.saved_journal_id and db.execute('SELECT 1 FROM journal WHERE id=? AND user_id=?',(p.saved_journal_id,s.user_id)).fetchone():return {'saved':True,'id':p.saved_journal_id,'duplicate':True}
                mid=str(uuid.uuid4())
                payload={'date':p.date,'look':p.name,'feeling':'','traits':'','reflection':json.dumps(summary,ensure_ascii=False),'session_id':s.session_id,'completed_step_count':len(summary['completed_steps']),'coaching_summary':summary}
                db.execute('INSERT INTO journal VALUES (?,?,?,?)',(mid,s.user_id,json.dumps(payload,ensure_ascii=False),datetime.now().astimezone().isoformat()))
                p.saved_journal_id=mid
                db.execute('UPDATE makeup_sessions SET payload=? WHERE session_id=? AND user_id=?',(p.model_dump_json(),s.session_id,s.user_id))
            s.makeup_plan=p
        return {'saved':True,'id':mid,'date':p.date,'transcript_saved':False,'media_saved':False}
    def mark_summary_presented(self,s,revision):
        with self.agent.memory.connect() as db:
            row=db.execute('SELECT payload FROM makeup_sessions WHERE session_id=? AND user_id=?',(s.session_id,s.user_id)).fetchone()
            if not row:return
            p=MakeupPlan.model_validate_json(row[0])
            if p.revision!=revision or p.status!='completed':return
            p.summary_presented=True
            db.execute('UPDATE makeup_sessions SET payload=? WHERE session_id=? AND user_id=?',(p.model_dump_json(),s.session_id,s.user_id))
        s.makeup_plan=p
    def handle(self,s,body):
        intent=coaching_intent(body.message)
        if not s.makeup_plan:
            if intent=='start' or (any(x in body.message.lower() for x in ('妆','makeup')) and any(x in body.message.lower() for x in ('想','want','准备'))):
                text=body.message.lower();minutes=re.search(r'(\d{1,3})\s*(?:分钟|minutes|min\b)',text)
                style=next((key for key,words in [('beginner',('初学','beginner')),('warm',('暖','warm')),('professional',('通勤','professional')),('evening',('晚','evening'))] if any(w in text for w in words)),'natural')
                self.create(s,{'style':style,'aesthetic':body.message[:400],'minutes':max(3,min(120,int(minutes[1]))) if minutes else 15})
                if intent!='start':return {'plan':s.makeup_plan.model_dump(),'needs_start_confirmation':True}
            else:return None
        if intent=='save':return self.save(s,body.message)
        if intent in ('advance','start','pause','resume','previous','blush','finish','repeat','explain','visual','skip'):
            if intent=='advance' and s.makeup_plan.status=='draft':intent='start'
            if intent=='advance' and s.makeup_plan.workflow=='PAUSED':intent='resume'
            result=self.act(s,intent,body.event_id,body.expected_step_id)
            if s.makeup_plan.status=='completed':result['summary']=self.summary(s)
            return result
        return {'plan':s.makeup_plan.model_dump(),'step':self.current(s),'state_unchanged':True}
