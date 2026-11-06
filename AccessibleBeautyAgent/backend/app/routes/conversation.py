import json
from fastapi import APIRouter,Request
from fastapi.responses import StreamingResponse
from app.schemas.models import ChatRequest

def build_conversation_router(service):
    router=APIRouter(prefix='/api')
    @router.post('/chat/stream')
    async def stream(body:ChatRequest,request:Request):
        if body.session_id:service.agent.sessions.get(body.session_id)
        async def events():
            async for item in service.stream(body,request):
                yield 'data: '+json.dumps(item,ensure_ascii=False)+'\n\n'
        return StreamingResponse(events(),media_type='text/event-stream',headers={'Cache-Control':'no-store','X-Accel-Buffering':'no'})
    @router.get('/transcripts/{session_id}')
    def transcript(session_id:str):
        service.agent.sessions.get(session_id)
        return {'messages':service.history(session_id),'persisted':False}
    @router.get('/diagnostics')
    def diagnostics(request:Request):
        prefix=request.state.principal_prefix
        owned={sid for sid,s in service.agent.sessions.sessions.items() if s.user_id.startswith(prefix)}
        rows=[{k:v for k,v in r.items() if k!='session_id'} for r in service.metrics if r['session_id'] in owned]
        return {'turns':rows,'sample_count':len(rows),'scope':'current_browser','cost_estimate':None,'notice':'Latency and usage are actual measurements; no provider price or visual accuracy estimate is configured.'}
    return router
