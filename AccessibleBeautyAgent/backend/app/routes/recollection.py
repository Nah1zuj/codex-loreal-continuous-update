import hashlib,uuid
from fastapi import APIRouter,Request
from pydantic import BaseModel,ConfigDict,Field,StrictBool

class ExperienceCommand(BaseModel):
    model_config=ConfigDict(extra='forbid')
    session_id:str|None=None
    locale:str='zh-CN'
    reuse_previous:bool=False
    event_id:str|None=Field(default=None,min_length=1,max_length=80)
    expected_step_id:str|None=Field(default=None,min_length=1,max_length=120)
    expected_plan_id:str|None=Field(default=None,min_length=1,max_length=80)
    expected_revision:int|None=Field(default=None,ge=0)

class RecallSetting(BaseModel):
    model_config=ConfigDict(extra='forbid')
    enabled:bool

class SummaryEdits(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    name:str|None=Field(default=None,min_length=1,max_length=100)
    note:str|None=Field(default=None,max_length=1200)


class SummaryDecision(BaseModel):
    model_config=ConfigDict(extra='forbid')
    version:str=Field(pattern=r'^[a-f0-9]{64}$')
    edits:SummaryEdits=Field(default_factory=SummaryEdits)
    explicit_consent:StrictBool=False


class SummaryConsent(BaseModel):
    model_config=ConfigDict(extra='forbid')
    explicit_consent:StrictBool


def build_recollection_router(agent):
    router=APIRouter(prefix='/api')
    def owner(request,user_id=None):
        prefix=request.state.principal_prefix
        if user_id is not None and not user_id.startswith(prefix):
            raise KeyError('Summary owner not found')
        return user_id or prefix+hashlib.sha256(b'demo').hexdigest()[:24]

    def subject(request,candidate_id):
        return agent.recollection.subject(candidate_id,request.state.principal_prefix)
    @router.get('/recollection')
    def view(request:Request,user_id:str|None=None):return agent.recollection.view(owner(request,user_id))
    @router.post('/recollection/settings')
    def setting(body:RecallSetting,request:Request):return agent.recollection.setting(owner(request),body.enabled)
    @router.delete('/recollection')
    def clear(request:Request):return agent.recollection.clear(owner(request))
    @router.get('/recollection/candidate/{session_id}')
    def candidate(session_id:str,request:Request):
        candidate_id=f'plan:{session_id}'
        return agent.recollection.prepare(subject(request,candidate_id),candidate_id)

    @router.post('/recollection/candidates/{candidate_id}/preview')
    def preview(candidate_id:str,body:SummaryEdits,request:Request):
        return agent.recollection.prepare(subject(request,candidate_id),candidate_id,body.model_dump(exclude_none=True))

    @router.post('/recollection/candidates/{candidate_id}/confirm')
    def confirm(candidate_id:str,body:SummaryDecision,request:Request):
        if body.explicit_consent is not True:
            raise PermissionError('请先审阅并确认这份摘要。')
        return agent.recollection.decide(subject(request,candidate_id),candidate_id,body.version,
                                        body.edits.model_dump(exclude_none=True),save=True)

    @router.post('/recollection/candidates/{candidate_id}/reject')
    def reject(candidate_id:str,body:SummaryDecision,request:Request):
        return agent.recollection.decide(subject(request,candidate_id),candidate_id,body.version,
                                        body.edits.model_dump(exclude_none=True),save=False)

    @router.post('/recollection/{record_id}/reuse')
    def reuse(record_id:str,body:SummaryConsent,request:Request):
        if body.explicit_consent is not True:
            raise PermissionError('请确认要沿用这份摘要的风格。')
        return agent.recollection.select(subject(request,record_id),record_id)

    @router.delete('/recollection/{record_id}')
    def remove(record_id:str,body:SummaryConsent,request:Request):
        if body.explicit_consent is not True:
            raise PermissionError('请明确确认删除这份摘要。')
        return agent.recollection.remove(subject(request,record_id),record_id)

    @router.post('/experience/reflect')
    def reflect(body:ExperienceCommand,request:Request):
        with agent.sessions.lock:
            s=agent.sessions.get(body.session_id) if body.session_id else agent.sessions.create(owner(request))
            s.locale='en' if body.locale=='en' else 'zh-CN'
            if s.makeup_plan and s.makeup_plan.status=='completed':
                return completed_reply(s)
            if not s.makeup_plan:
                style=agent.recollection.reusable_style(s.user_id) if body.reuse_previous else 'natural'
                agent.coaching.create(s,{'style':style,'occasion':s.scene or 'daily','aesthetic':' '.join(s.desired_impression)[:400]})
            if s.makeup_plan.status=='draft':agent.coaching.act(s,'start',str(uuid.uuid4()))
            elif s.makeup_plan.workflow=='PAUSED':agent.coaching.act(s,'resume',str(uuid.uuid4()))
            instruction=agent.current_step(s)['instruction']
            intro='现在是第三步，映照。一次做一个步骤。说下一步、再说一次或跳过；结束本次装扮可随时说出。' if s.locale=='zh-CN' else 'Step three, Reflect. Say next, repeat or skip. Say finish this look to end the experience. '
            return agent.respond(s,intro+instruction)
    @router.post('/recollection/finish')
    def finish(body:ExperienceCommand,request:Request):
        if not body.session_id:raise ValueError('尚未开始装扮，可以先进入倾听。')
        with agent.sessions.lock:
            s=agent.sessions.get(body.session_id)
            if not s.makeup_plan or s.makeup_plan.status=='draft':raise ValueError('还没有开始映照步骤，请先完成倾听。')
            result=None
            if s.makeup_plan.status!='completed' or body.event_id:
                result=agent.coaching.act(s,'finish',body.event_id,body.expected_step_id,
                                          expected_plan_id=body.expected_plan_id,expected_revision=body.expected_revision)
            reply=completed_reply(s)
            if result:reply['event']=result['event']
            return reply

    def completed_reply(s):
        summary=agent.coaching.summary(s)
        count=len(summary['completed_steps'])
        name=summary['chosen_look']
        if s.locale=='zh-CN':
            text=f'本次{name}体验已结束。你确认完成了{count}个步骤。可到拾光查看并决定是否保存摘要。'
        else:
            text=f'Your {name} experience has ended with {count} confirmed steps. Open Trace to review and decide whether to save the summary.'
        try:
            candidate=agent.recollection.prepare(s.user_id,f'plan:{s.session_id}')
        except KeyError:
            candidate=None
        return {**agent.respond(s,text),'summary':summary,'summary_candidate':candidate,'recollection':None}
    return router
