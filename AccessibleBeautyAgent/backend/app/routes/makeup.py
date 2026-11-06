from fastapi import APIRouter
from pydantic import BaseModel,StrictBool,ConfigDict

class DeletePlan(BaseModel):
    model_config=ConfigDict(extra='forbid')
    explicit_consent:StrictBool=False

def build_makeup_router(agent):
    router=APIRouter(prefix='/api/makeup')
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
            s.makeup_plan=None;s.routine_started=False;s.routine_step=0;s.visual_state=None
            agent.sessions.stop(s)
        return {'deleted':True,'journal_deleted':False}
    return router
