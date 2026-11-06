from fastapi import APIRouter,Request
from app.schemas.makeup import CoachingCommand
from app.agent.coaching import RoutineUnavailable
from pydantic import BaseModel,StrictBool,ConfigDict

class DeletePlan(BaseModel):
    model_config=ConfigDict(extra='forbid')
    explicit_consent:StrictBool=False

def build_makeup_router(agent):
    router=APIRouter(prefix='/api/makeup')
    @router.post('/command')
    def command(body:CoachingCommand):
        with agent.sessions.lock:
            s=agent.sessions.get(body.session_id)
            result=agent.coaching.act(
                s,body.action,body.event_id,body.expected_step_id,
                expected_plan_id=body.expected_plan_id,expected_revision=body.expected_revision,
            )
            if result.get('duplicate'):
                return agent.duplicate_reply(s, result)
            step=result['step']
            if s.makeup_plan.status=='completed':
                message='本次装扮体验已结束。' if s.locale=='zh-CN' else 'This look experience has ended.'
            elif s.makeup_plan.workflow=='PAUSED':
                message='已暂停，步骤保留。' if s.locale=='zh-CN' else 'Paused. Your step is preserved.'
            else:
                message=step['instruction'] if step else ''
            reply=agent.respond(s,message)
            if s.makeup_plan.status=='completed':
                reply['summary']=agent.coaching.summary(s)
            return {**reply,'event':result['event'],'duplicate':result.get('duplicate',False)}

    @router.get('/events/{session_id}/{event_id}')
    def event(session_id:str,event_id:str,request:Request):
        with agent.sessions.lock:
            s=agent.sessions.get(session_id)
            if not s.user_id.startswith(request.state.principal_prefix):
                raise KeyError('Session not found')
            result=agent.coaching.event(s,event_id)
            if result is None:
                raise KeyError('Command not found')
            try:
                current_step = agent.current_step(s)
            except RoutineUnavailable:
                current_step = None
            return {'event':result,'session':{**s.model_dump(),'current_step':current_step}}

    @router.get('/{session_id}')
    def get(session_id:str):
        s=agent.sessions.get(session_id)
        return {'plan':s.makeup_plan,'current_step':agent.coaching.current(s),'persistence_days':30}
    @router.delete('/{session_id}')
    def remove(session_id:str,body:DeletePlan):
        if body.explicit_consent is not True:raise PermissionError('Confirm deletion of this coaching progress')
        with agent.sessions.lock:
            s=agent.sessions.get(session_id)
            with agent.memory.connect() as db:
                db.execute('DELETE FROM makeup_events WHERE session_id=?',(session_id,))
                db.execute('DELETE FROM makeup_sessions WHERE session_id=? AND user_id=?',(session_id,s.user_id))
            s.makeup_plan = None
            s.routine_id = None
            s.proposed_routine_step_count = 0
            agent.sessions.stop(s)
        return {'deleted':True,'journal_deleted':False}
    return router
