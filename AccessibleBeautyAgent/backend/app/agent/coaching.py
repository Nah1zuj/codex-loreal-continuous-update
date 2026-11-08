"""Durable, owner-scoped coaching. No transcript, images or consent persisted here."""
import json,re,time,uuid
from datetime import datetime
from app.agent.coaching_intents import coaching_intent
from app.agent.coaching_needs import next_clarification, provided_needs, requested_coaching
from app.agent.providers import MockLanguageProvider
from app.knowledge.curriculum import TEMPLATES, course_options, lesson_rows, make_steps, select_course
from app.schemas.makeup import LegacyRoutineRef, LegacyRoutineStep, MakeupPlan, PlanNeeds
from app.schemas.models import Stage


class CommandConflict(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


class RoutineUnavailable(ValueError):
    """A pinned legacy routine changed or is no longer eligible."""


class CoachingController:
    def __init__(self,agent):self.agent=agent

    @staticmethod
    def unavailable_course():
        return CommandConflict('COURSE_UNAVAILABLE','课程尚未通过试用审核，或版本已变更。请返回并选择可用课程。')

    def visible_plan(self, session):
        plan = session.makeup_plan
        return plan if plan and self.course_available(plan) else None

    def knowledge(self, locale, reviewed_only=True):
        return lesson_rows(self.agent.store, locale, reviewed_only=reviewed_only)

    def course_rows(self, locale, needs):
        rows = self.knowledge(locale)
        if all(course_options(rows, needs)):
            return rows, True
        if not self.agent.settings.developer_mode:
            raise ValueError('Expert-reviewed makeup lessons are not available')
        return self.knowledge(locale, False), False

    def proposal_options(self, s):
        rows, _ = self.course_rows(s.locale, s.makeup_plan.needs)
        return [[row['guidance_id'] for row in options]
                for options in course_options(rows, s.makeup_plan.needs)]

    def create(self, s, needs, candidate=None, *, expected_draft=None):
        needs = PlanNeeds.model_validate(needs)
        with self.agent.sessions.lock:
            current = s.makeup_plan
            if current and current.status == 'active':
                raise ValueError('Finish the active plan before replacing it')
            if expected_draft and (
                current is None or current.status != 'draft' or (current.id, current.revision) != expected_draft
            ):
                raise CommandConflict('STALE_PLAN','教学进度已变化。请读取最新步骤后再操作。')
            rows, reviewed = self.course_rows(s.locale, needs)
            selected, fallback = select_course(rows, needs, candidate)
            if not selected:
                raise ValueError('Curriculum coverage missing; active state unchanged')
            steps = make_steps(selected, self.agent.store.sources)
            if expected_draft and candidate is not None:
                if fallback:
                    raise ValueError('Invalid curriculum candidate')
                if current.steps == steps:
                    return current
            plan = MakeupPlan(
                id=str(uuid.uuid4()), userId=s.user_id, sessionId=s.session_id,
                name=TEMPLATES[needs.style][0 if s.locale=='zh-CN' else 1], occasion=needs.occasion,
                styleDescription=needs.aesthetic or needs.style, estimatedMinutes=needs.minutes,
                needs=needs, steps=steps, date=datetime.now().astimezone().date().isoformat(),
                generation_status='fallback' if fallback else 'grounded',
                knowledge_status='reviewed' if reviewed else 'draft',
            )
            with self.agent.memory.connect() as db:
                db.execute('INSERT OR REPLACE INTO makeup_sessions VALUES (?,?,?,?,?)',
                           (s.session_id,s.user_id,s.locale,plan.model_dump_json(),time.time()))
            s.makeup_plan=plan
            self.agent.sessions.project_plan(s)
            return plan

    def legacy_plan(self, session, routine_id):
        """Adapt the selected catalogue routine on first explicit start."""
        routine = self.agent.require_available_routine(routine_id, session)
        look = self.agent.store.look_map[routine['look_id']]
        occasion = session.scene or 'daily'
        return MakeupPlan(
            id=str(uuid.uuid4()), userId=session.user_id, sessionId=session.session_id,
            name=routine.get('name') or look['name'], occasion=occasion,
            styleDescription=look['name'], estimatedMinutes=PlanNeeds().minutes,
            needs=PlanNeeds(occasion=occasion),
            steps=[
                LegacyRoutineStep(id=row['step_id'], title=row['name'], order=index,
                                  optionalVisualCheck=row.get('visual_task'))
                for index, row in enumerate(routine['steps'], start=1)
            ],
            legacy_routine=LegacyRoutineRef(routine_id=routine_id, look_id=look['look_id'],
                                            version=routine['version']),
            date=datetime.now().astimezone().date().isoformat(),
            knowledge_status='reviewed' if routine.get('verified') and not routine.get('demo_data') else 'draft',
        )

    def legacy_routine(self, session, plan):
        ref = plan.legacy_routine
        routine = self.agent.require_available_routine(
            ref.routine_id, session, expected_version=ref.version, expected_look=ref.look_id,
        )
        if [step.id for step in plan.steps] != [row['step_id'] for row in routine['steps']]:
            self.agent.disable_routine(session)
        return routine

    def current(self,s):
        p=s.makeup_plan
        if not p or p.status=='draft' or p.status=='completed':return None
        if s.routine_unavailable:return None
        step=p.steps[p.active_index]
        if p.legacy_routine:
            routine = self.legacy_routine(s, p)
            return {**routine['steps'][p.active_index], 'status': step.status,
                    'source_id': p.legacy_routine.routine_id, 'review_status': routine['status']}
        if not self.course_available(p):
            return None
        localized_id=re.sub(r'_(zh|en)$','_zh' if s.locale=='zh-CN' else '_en',step.source_id)
        lesson=step
        if localized_id!=step.source_id:
            row=next((row for row in self.knowledge(s.locale,p.knowledge_status=='reviewed')
                      if row['guidance_id']==localized_id),None)
            if row:
                lesson=make_steps([row],self.agent.store.sources)[0]
        prefix=('美没有统一的定义，按你喜欢的方式表达就好。' if s.locale=='zh-CN' else 'Beauty has no single definition. Express yourself in your own way. ') if p.knowledge_status=='draft' else ''
        return {
            'step_id':step.id,'name':lesson.title,
            'instruction':prefix+' '.join(lesson.preparation+lesson.instructions+lesson.accessibilityInstructions),
            'instruction_repeat':prefix+' '.join(lesson.instructions),
            'instruction_slow':prefix+' '.join(lesson.instructions+lesson.commonMistakes),
            'explanation_why':lesson.purpose,'visual_check_required':False,'visual_task':lesson.optionalVisualCheck,
            'status':step.status,'source_id':lesson.source_id,'review_status':lesson.review_status,
            'lesson_provenance':lesson.lesson_provenance.model_dump(mode='json') if lesson.lesson_provenance else None,
        }

    def course_available(self, plan):
        if plan.legacy_routine or self.agent.settings.developer_mode:
            return True
        if plan.knowledge_status!='reviewed':
            return False
        versions={row['guidance_id']:row['version'] for locale in ('zh-CN','en') for row in self.knowledge(locale)}
        return all(step.lesson_provenance and versions.get(step.source_id)==step.lesson_provenance.version
                   for step in plan.steps)

    def event(self,s,event_id):
        with self.agent.memory.connect() as db:
            row=db.execute(
                'SELECT e.intent,r.details FROM makeup_events e JOIN makeup_sessions p ON p.session_id=e.session_id '
                'LEFT JOIN makeup_event_receipts r ON r.session_id=e.session_id AND r.event_id=e.event_id '
                'WHERE e.session_id=? AND p.user_id=? AND e.event_id=?',
                (s.session_id,s.user_id,event_id),
            ).fetchone()
        if row is None:
            return None
        details=json.loads(row[1]) if row[1] else {}
        return {'event_id':event_id,'action':row[0],'status':'committed',**details.get('result',{})}

    def act(self,s,intent,event_id=None,expected_step_id=None,*,expected_plan_id=None,expected_revision=None,compatible_next=False,initial_plan=None):
        event_id=event_id or str(uuid.uuid4())
        expectation={'plan_id':expected_plan_id,'revision':expected_revision,'step_id':expected_step_id}
        with self.agent.sessions.lock:
            with self.agent.memory.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                row=db.execute('SELECT payload FROM makeup_sessions WHERE session_id=? AND user_id=?',(s.session_id,s.user_id)).fetchone()
                if not row and initial_plan is None:raise ValueError('No plan for this owner')
                p=MakeupPlan.model_validate_json(row[0]) if row else initial_plan
                previous=db.execute(
                    'SELECT e.intent,r.details FROM makeup_events e LEFT JOIN makeup_event_receipts r '
                    'USING(session_id,event_id) WHERE e.session_id=? AND e.event_id=?',
                    (s.session_id,event_id),
                ).fetchone()
                if previous:
                    details=json.loads(previous[1]) if previous[1] else {}
                    if previous[0]!=intent or (details and details['expected']!=expectation):
                        raise CommandConflict('EVENT_MISMATCH','此事件已用于其他操作。请刷新当前步骤。')
                    if s.makeup_plan!=p:
                        s.makeup_plan=p
                        self.agent.sessions.project_plan(s)
                    try:
                        step = self.current(s)
                    except RoutineUnavailable:
                        step = None
                    return {'duplicate':True,'plan':p.model_dump() if self.course_available(p) else None,'step':step,'event':{
                        'event_id':event_id,'action':intent,'status':'committed',**details.get('result',{}),
                    }}
                if ((expected_plan_id is not None and expected_plan_id!=p.id)
                        or (expected_revision is not None and expected_revision!=p.revision)
                        or (expected_step_id is not None and expected_step_id!=p.steps[p.active_index].id)):
                    raise CommandConflict('STALE_PLAN','教学进度已变化。请读取最新步骤后再操作。')
                available = self.course_available(p)
                if not available and intent not in ('finish', 'end_session'):
                    raise self.unavailable_course()
                requested=intent
                if compatible_next and intent=='advance':
                    if p.status=='draft':intent='start'
                    elif p.workflow=='PAUSED':intent='resume'
                if p.session_ended and intent not in ('finish', 'end_session'):
                    raise ValueError('本次会话已经结束。可以开始新会话。')
                if p.legacy_routine and p.status != 'completed' and intent not in ('finish', 'end_session'):
                    self.legacy_routine(s, p)
                    if s.stage in {Stage.CHECK_REQUESTED, Stage.CAMERA_CONSENT, Stage.VISION_GATE, Stage.VISION_CHECK} and intent in ('start','advance','skip','previous','blush'):
                        raise ValueError('请先结束当前相机检查。')
                if intent in ('repeat','explain','visual'):
                    if intent=='visual':
                        s.visual_state=None
                        s.confidence=0
                    return {'plan':p.model_dump(),'step':self.current(s),'visual_request':intent=='visual',
                            'frame_obtained':False if intent=='visual' else None}
                before=p.model_dump()
                if intent=='start':
                    if p.status=='completed':raise ValueError('Session is complete')
                    if p.workflow=='PAUSED':raise ValueError('Resume the paused plan before continuing')
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
                elif intent in ('finish', 'end_session'):
                    # User ending early does not claim unperformed steps are completed.
                    if available and p.status=='draft' and intent=='finish':raise ValueError('Start the plan before finishing')
                    p.status='completed';p.workflow='SESSION_COMPLETE'
                    if intent == 'end_session':
                        p.session_ended = True
                else:raise ValueError('Unknown action')
                changed=p.model_dump()!=before
                if changed:
                    p.revision+=1
                    p.summary_presented=False
                    if row:
                        db.execute('UPDATE makeup_sessions SET payload=?,locale=?,updated_at=? WHERE session_id=? AND user_id=?',
                                   (p.model_dump_json(),s.locale,time.time(),s.session_id,s.user_id))
                    else:
                        db.execute('INSERT INTO makeup_sessions VALUES (?,?,?,?,?)',
                                   (s.session_id,s.user_id,s.locale,p.model_dump_json(),time.time()))
                result={'plan_id':p.id,'revision':p.revision,'step_id':p.steps[p.active_index].id,
                        'plan_status':p.status,'workflow':p.workflow}
                db.execute('INSERT INTO makeup_events(session_id,event_id,intent) VALUES (?,?,?)',
                           (s.session_id,event_id,requested))
                db.execute('INSERT INTO makeup_event_receipts(session_id,event_id,details) VALUES (?,?,?)',
                           (s.session_id,event_id,json.dumps({'expected':expectation,'result':result})))
            if s.makeup_plan != p:
                s.makeup_plan = p
                self.agent.sessions.project_plan(s)
            if changed and (intent in ('pause','resume','finish','end_session') or p.status=='completed'
                            or (p.legacy_routine and intent in ('advance','skip','previous','blush'))):
                self.agent.sessions.revoke_media(s)
            return {'plan':p.model_dump() if available else None,'step':self.current(s),'event':{
                'event_id':event_id,'action':requested,'status':'committed',**result,
            }}
    def summary(self,s):
        p=s.makeup_plan
        if not p or p.status!='completed':raise ValueError('Finish the session before summarizing')
        if not self.course_available(p):
            return None
        completed = [step for step in p.steps if step.status == 'completed']
        if p.legacy_routine:
            source = self.agent.store.routine_map.get(p.legacy_routine.routine_id, {})
            instructions = {row['step_id']:row['instruction'] for row in source['steps']} if source.get('version') == p.legacy_routine.version else {}
            practiced = [instructions[step.id] for step in completed if step.id in instructions]
        else:
            practiced = [' '.join(step.instructions) for step in completed]
        return {'chosen_look':p.name,'date':p.date,'completed_steps':[step.title for step in completed],'techniques_practiced':practiced,'preferences':{},'feelings':None,'observations':None,'future_advice':'下次可重复尚不熟悉的步骤。' if s.locale=='zh-CN' else 'Practice an unfamiliar step next time.','knowledge_status':p.knowledge_status,'requires_confirmation':True}
    def save(self,s,user_text):
        if coaching_intent(user_text)!='save':raise PermissionError('Explicit journal confirmation required')
        if not s.makeup_plan or not s.makeup_plan.summary_presented:raise PermissionError('Read the completed session summary before saving')
        summary=self.summary(s)
        if summary is None:raise self.unavailable_course()
        with self.agent.sessions.lock:
            with self.agent.memory.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                row=db.execute('SELECT payload FROM makeup_sessions WHERE session_id=? AND user_id=?',(s.session_id,s.user_id)).fetchone()
                if not row:raise PermissionError('Plan owner mismatch')
                p=MakeupPlan.model_validate_json(row[0])
                if p.saved_journal_id:
                    existing = db.execute('SELECT 1 FROM journal WHERE id=? AND user_id=?',
                                          (p.saved_journal_id,s.user_id)).fetchone()
                    if existing:
                        return {'saved':True,'id':p.saved_journal_id,'duplicate':True}
                    message = ('这份已确认的日志已删除。你可以在拾光重新撰写并确认一份日志。'
                               if s.locale=='zh-CN' else
                               'This confirmed journal entry was deleted. Open Trace to write and confirm a new entry.')
                    raise CommandConflict('JOURNAL_SAVE_REVOKED',message)
                payload={'date':p.date,'look':p.name,'feeling':'','traits':'','reflection':json.dumps(summary,ensure_ascii=False),'session_id':s.session_id,'completed_step_count':len(summary['completed_steps']),'coaching_summary':summary}
                record=self.agent.journal.insert(db,s.user_id,payload)
                mid=record['id']
                p.saved_journal_id=mid
                db.execute('UPDATE makeup_sessions SET payload=? WHERE session_id=? AND user_id=?',(p.model_dump_json(),s.session_id,s.user_id))
            s.makeup_plan=p
        return {'saved':True,'id':mid,'date':p.date,'transcript_saved':False,'media_saved':False}
    def mark_summary_presented(self,s,revision):
        with self.agent.memory.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT payload FROM makeup_sessions WHERE session_id=? AND user_id=?',(s.session_id,s.user_id)).fetchone()
            if not row:return
            p=MakeupPlan.model_validate_json(row[0])
            if p.revision!=revision or p.status!='completed':return
            p.summary_presented=True
            db.execute('UPDATE makeup_sessions SET payload=? WHERE session_id=? AND user_id=?',(p.model_dump_json(),s.session_id,s.user_id))
        s.makeup_plan=p
    def handle(self,s,body):
        intent=coaching_intent(body.message)
        if s.makeup_plan and intent!='finish' and self.visible_plan(s) is None:
            raise self.unavailable_course()
        if intent=='ambiguous' and s.makeup_plan:
            return {'clarification_required':True,'state_unchanged':True}
        if not s.makeup_plan:
            if s.routine_id and intent in ('start','advance'):
                return None
            initial=requested_coaching(body.message)
            if intent!='start' and not initial:
                return None
            plan=self.create(s,provided_needs(body.message,initial=initial) or PlanNeeds())
            if intent!='start':
                return self.draft_reply(plan,s.locale)
        elif s.makeup_plan.status=='draft' and not s.makeup_plan.legacy_routine:
            if needs:=provided_needs(body.message,current=s.makeup_plan.needs):
                current=s.makeup_plan
                if ((body.expected_plan_id is not None and body.expected_plan_id!=current.id)
                        or (body.expected_revision is not None and body.expected_revision!=current.revision)):
                    raise CommandConflict('STALE_PLAN','教学进度已变化。请读取最新步骤后再操作。')
                if needs!=current.needs:
                    current=self.create(s,needs,expected_draft=(current.id,current.revision))
                return self.draft_reply(current,s.locale)
        if intent=='save':return self.save(s,body.message)
        if intent in ('advance','start','pause','resume','previous','blush','finish','repeat','explain','visual','skip'):
            result=self.act(s,intent,body.event_id,body.expected_step_id,
                            expected_plan_id=body.expected_plan_id,expected_revision=body.expected_revision,
                            compatible_next=True)
            if s.makeup_plan.status=='completed' and (summary:=self.summary(s)) is not None:
                result['summary']=summary
            return result
        return {'plan':s.makeup_plan.model_dump(),'step':self.current(s),'state_unchanged':True}

    def draft_reply(self, plan, locale):
        return {'plan':plan.model_dump(mode='json'),'needs_start_confirmation':True,
                'clarification':next_clarification(plan.needs,locale)}

    def reply_text(self, s, data, intent, text):
        zh = s.locale == 'zh-CN'
        if data.get('clarification_required'):
            return ('我会保留这一步。你想听当前步骤的说明，还是已经做完、准备进入下一步？'
                    if zh else 'Your step is unchanged. Would you like an explanation, or have you finished and want the next step?')
        plan = s.makeup_plan
        if plan.status=='completed' and self.visible_plan(s) is None:
            return '本次装扮体验已结束。' if zh else 'This look experience has ended.'
        label = ('待审核原创课程。' if zh else 'Original draft curriculum awaiting expert review. ') if (
            plan.knowledge_status == 'draft' and not data.get('state_unchanged')
        ) else ''
        if data.get('saved'):
            return label + ('私人记录已保存。' if zh else 'Your private record was saved.')
        if summary := data.get('summary'):
            steps = summary['completed_steps']
            if zh:
                completed = '你确认完成了' + '、'.join(steps) + '。' if steps else '本次没有确认完成的步骤。'
                return label + '本次教学已结束。' + completed + '是否保存到我的记录？'
            completed = 'You confirmed: ' + ', '.join(steps) + '. ' if steps else 'No steps were confirmed complete. '
            return label + 'The lesson has ended. ' + completed + 'Save to your records?'
        if data.get('visual_request'):
            return label + ('请开启摄像头并同意本地单帧检查。尚未获得新画面。' if zh else
                            'Enable the camera and allow a local single-frame check. No fresh frame has been obtained.')
        if data.get('needs_start_confirmation'):
            prompt = data['clarification'] or ('准备好时说“开始”。' if zh else 'Say “start” when ready.')
            return label + plan.name + ('。' if zh else '. ') + prompt
        if intent=='chat' and data.get('state_unchanged'):
            return MockLanguageProvider().companion(text,s.last_response,s.locale)
        step = data.get('step')
        if step and intent in ('repeat','explain'):
            return label + step['instruction_repeat' if intent=='repeat' else 'explanation_why']
        if plan.workflow=='PAUSED':
            return label + ('已暂停，步骤保留。' if zh else 'Paused; your step is preserved.')
        return label + (step['instruction'] if step else plan.name)
