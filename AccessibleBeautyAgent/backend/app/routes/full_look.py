from fastapi import APIRouter, HTTPException
from app.full_look.service import LookVersionConflict
from app.schemas.full_look import PlanRequest,RevisionRequest,ConfirmationRequest,PlanMemoryRequest,MaterialQuery

def build_full_look_router(agent):
    router=APIRouter(prefix='/api')
    def reply(s,message,**extra):return {**agent.respond(s,message),**extra}
    @router.post('/full-look/plan')
    def plan(body:PlanRequest):
        with agent.sessions.lock:
            s=agent.sessions.get(body.session_id);p=agent.full_look.plan(s)
            return reply(s,agent.full_look.summary(s),plan=p.model_dump())
    @router.get('/full-look/{session_id}')
    def get(session_id:str):
        with agent.sessions.lock:
            s=agent.sessions.get(session_id);return {'plan':agent.full_look.get(s).model_dump(),'session':s.model_dump()}
    @router.post('/full-look/revise')
    def revise(body:RevisionRequest):
        with agent.sessions.lock:
            s=agent.sessions.get(body.session_id)
            try:
                r=agent.full_look.revise(s,body)
            except LookVersionConflict as conflict:
                raise HTTPException(409, {'code':'FULL_LOOK_CONFLICT','current_version':conflict.version,'plan_id':conflict.plan_id}) from conflict
            return reply(s,' '.join(r['reasons'])+' '+ ' '.join(s.todays_look.pending_coordination),**r)
    @router.post('/full-look/confirm')
    def confirm(body:ConfirmationRequest):
        with agent.sessions.lock:
            s=agent.sessions.get(body.session_id)
            try:
                p=agent.full_look.confirm(s,body)
            except LookVersionConflict as conflict:
                raise HTTPException(409, {'code':'FULL_LOOK_CONFLICT','current_version':conflict.version,'plan_id':conflict.plan_id}) from conflict
            return reply(s,'本次造型选择已更新；没有保存长期记忆。',plan=p.model_dump())
    @router.post('/full-look/memory-candidate')
    def candidate(body:PlanMemoryRequest):
        with agent.sessions.lock:
            s=agent.sessions.get(body.session_id);agent.full_look.memory_candidate(s,body.feedback)
            return reply(s,'希望把这些明确选择留到下次吗？请查看候选后选择保存或不保存。')
    @router.get('/materials')
    def materials():return {'results':agent.full_look.materials.rows}
    @router.post('/materials/explain')
    def explain(body:MaterialQuery):return agent.full_look.materials.explain(body.material_ids)
    return router
