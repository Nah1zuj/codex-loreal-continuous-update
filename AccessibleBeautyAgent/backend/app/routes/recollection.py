import hashlib,uuid
from fastapi import APIRouter,Request
from pydantic import BaseModel,ConfigDict

class ExperienceCommand(BaseModel):
    model_config=ConfigDict(extra='forbid')
    session_id:str|None=None
    locale:str='zh-CN'
    reuse_previous:bool=False

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
            if s.makeup_plan and s.makeup_plan.status=='completed':s=agent.sessions.create(s.user_id);s.locale=body.locale
            if not s.makeup_plan:
                previous=agent.recollection.view(s.user_id)
                style=previous['latest']['style'] if body.reuse_previous and previous['enabled'] and previous['latest'] else 'natural'
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
            if s.makeup_plan.status!='completed':agent.coaching.act(s,'finish',str(uuid.uuid4()))
            record=agent.recollection.remember(s)
            count=sum(step.status=='completed' for step in s.makeup_plan.steps)
            verb='尝试了' if count else '聊到了'
            text=f'今天的装扮体验告一段落。我们{verb}{s.makeup_plan.name}，你确认完成了{count}个步骤。下次见面，我会自然接续今天的妆容。你仍可以说话、打开其他页面，或说请终止对话安静等待。' if s.locale=='zh-CN' else f'Your {s.makeup_plan.name} experience is complete, with {count} confirmed steps. I will remember the look for next time. You can continue using voice or pause replies.'
            if record is None:text=text.replace('下次见面，我会自然接续今天的妆容。','').replace(' I will remember the look for next time.','')
            return {**agent.respond(s,text),'recollection':record}
    return router
