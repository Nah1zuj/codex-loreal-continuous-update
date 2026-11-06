import hashlib,uuid
from fastapi import APIRouter,Request
from pydantic import BaseModel,ConfigDict,Field

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

def build_recollection_router(agent):
    router=APIRouter(prefix='/api')
    def owner(request):return request.state.principal_prefix+hashlib.sha256(b'demo').hexdigest()[:24]
    @router.get('/recollection')
    def view(request:Request):return agent.recollection.view(owner(request))
    @router.post('/recollection/settings')
    def setting(body:RecallSetting,request:Request):return agent.recollection.setting(owner(request),body.enabled)
    @router.delete('/recollection')
    def clear(request:Request):return agent.recollection.clear(owner(request))
    @router.post('/experience/reflect')
    def reflect(body:ExperienceCommand,request:Request):
        with agent.sessions.lock:
            s=agent.sessions.get(body.session_id) if body.session_id else agent.sessions.create(owner(request))
            s.locale='en' if body.locale=='en' else 'zh-CN'
            if s.makeup_plan and s.makeup_plan.status=='completed':
                return completed_reply(s)
            if not s.makeup_plan:
                agent.coaching.create(s,{'style':'natural','occasion':s.scene or 'daily','aesthetic':' '.join(s.desired_impression)[:400]})
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
            text=f'本次{name}体验已结束。你确认完成了{count}个步骤。你可以继续交流，或打开私人日志。'
        else:
            text=f'Your {name} experience has ended with {count} confirmed steps. You can continue the conversation or open your private journal.'
        return {**agent.respond(s,text),'summary':summary,'recollection':None}
    return router
