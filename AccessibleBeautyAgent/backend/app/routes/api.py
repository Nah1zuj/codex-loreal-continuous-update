from app.content.locale import localize_view
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel,ConfigDict
from typing import Literal
import hashlib

class VisualSessionStart(BaseModel):
    model_config=ConfigDict(extra='forbid')
    locale:Literal['zh-CN','en']='zh-CN'
    experience_mode:Literal['visual']='visual'
from app.schemas.models import ChatRequest, LookRequest, ProductRequest, RoutineRequest, SearchRequest, VisionRequest, MemoryRequest, FeedbackRequest
from app.vision.gate import decode_image
from app.vision.local_landmarks import MODEL
from app.services.voice import BrowserVoiceFallback, QwenRealtimePlaceholder

def build_router(agent,settings):
    api = APIRouter(prefix='/api')
    @api.post('/session')
    def start_visual_session(body:VisualSessionStart,request:Request):
        # Session only: no LLM request, plan creation or camera/analysis grant.
        with agent.sessions.lock:
            s=agent.sessions.create(request.state.principal_prefix+hashlib.sha256(b'demo').hexdigest()[:24])
            s.locale=body.locale;s.experience_mode=body.experience_mode
            return s.model_dump()
    @api.get('/health')
    def health():
        remote_key = {
            'deepseek': settings.deepseek_api_key,
            'openai_compatible': settings.compatible_api_key,
            'qwen': settings.api_key,
        }.get(settings.model_provider)
        compatible_endpoint = settings.model_provider != 'openai_compatible' or (
            bool(settings.compatible_base_url) and bool(settings.compatible_model)
        )
        remote_ready = bool(settings.allow_remote_ai and remote_key and compatible_endpoint)
        memory_ready = agent.memory.healthy()
        rag_ready = bool(agent.retriever.documents)
        return {
            'experience_revision': 'harness-v2-20261017',
            'status': 'ok', 'backend': True, 'agent': True, 'rag': rag_ready,
            'vision': True, 'memory': memory_ready, 'provider_mode': settings.model_provider,
            'providers': {
                'language': settings.model_provider, 'vision': settings.vision_provider,
                'embedding': settings.embedding_provider, 'voice': settings.voice_provider,
            },
            'developer_mode': settings.developer_mode, 'research_mode': settings.research_mode,
            'allow_remote_ai': settings.allow_remote_ai, 'reading_provider': settings.reading_provider,
            'reference_provider': settings.reference_provider, 'policy_version': agent.policies.version,
            'policy_manifest': agent.policies.manifest(), 'remote_ready': remote_ready,
            'readiness': {
                'service_reachable': True,
                'sqlite_ready': memory_ready, 'knowledge_loaded': rag_ready,
                'vision_asset_present': MODEL.is_file(),
                'vision_inference_verified': False,
                'remote_text_configured': remote_ready, 'remote_text_verified': False,
            },
        }
    @api.post('/chat')
    def chat(body: ChatRequest):
        with agent.sessions.lock:
            return agent.chat(body)
    @api.get('/session/{session_id}')
    def session(session_id: str, locale: str | None = None):
        with agent.sessions.lock:
            s=agent.sessions.get(session_id)
            return localize_view({**s.model_dump(),'current_step':agent.current_step(s)},locale or 'zh-CN')
    @api.post('/look/search')
    def looks(body: LookRequest):
        return {'results':agent.retrieve_look(body.scene,body.desired_impression,body.avoid,body.preferences)}
    @api.post('/products/search')
    def products(body: ProductRequest):
        return {'results':agent.retrieve_products(body.look_id,body.scene,body.preferences)}
    @api.post('/products/compare')
    def compare(product_ids: list[str]):
        return {'results':agent.compare_products(product_ids)}
    @api.post('/rag/search')
    def rag(body: SearchRequest):
        return agent.retriever.search(body.query,body.filters,body.limit)
    @api.post('/routine/start')
    def start(body: RoutineRequest):
        with agent.sessions.lock:
            s = agent.sessions.get(body.session_id)
            step = agent.start_routine(body.routine_id or s.routine_id,s)
            return agent.respond(s,step['instruction'])
    @api.post('/routine/advance')
    def advance(body: RoutineRequest):
        with agent.sessions.lock:
            s = agent.sessions.get(body.session_id)
            step = agent.advance_routine(s.session_id)
            return agent.respond(s,step['instruction'] if step else '流程完成。你希望下次调整什么？')

    def authorize_images(body):
        s = agent.sessions.get(body.session_id)
        if not s.camera_consent:
            raise PermissionError('请先明确同意相机检查。')
        if body.demo and (not settings.developer_mode or settings.vision_provider!='mock'):
            raise PermissionError('模拟场景仅在 mock 开发模式可用。')
        if body.capture_kind == "video_sample" and settings.vision_provider != "mock" and not body.remote_frame_consent:
            raise PermissionError("Explicit remote frame consent required for video samples")
        try:
            images = [decode_image(x) for x in body.images]
        except ValueError as exc:
            raise HTTPException(422,str(exc)) from exc
        return s,images
    @api.post('/vision/gate')
    def gate(body: VisionRequest):
        with agent.sessions.lock:
            s,images = authorize_images(body)
            if body.demo:
                from app.vision.gate import demo_gate
                return demo_gate()
            if not images:
                raise HTTPException(422,'请提交至少一帧图片。')
            results = [agent.vision.gate.evaluate(x) for x in images]
            return {**next((r for r in results if not r['gate_pass']),results[0]),'frames':results}
    @api.post('/vision/check')
    def check(body: VisionRequest):
        with agent.sessions.lock:
            s,images = authorize_images(body)
            result = agent.run_visual_check(body.task,images,{'session_id':s.session_id,'selected_look':s.selected_look,'mock_status':body.mock_status,'capture_kind':body.capture_kind},demo=body.demo)
            return {**result,'session':s.model_dump(),'step':agent.current_step(s)}
    @api.get('/profile/{user_id}')
    def profile(user_id: str):
        return agent.get_user_profile(user_id)
    @api.post('/memory')
    def memory(body: MemoryRequest):
        return agent.save_memory(body.user_id,body.candidate.model_dump(),body.explicit_consent)
    @api.post('/memory/{memory_id}/edit')
    def edit_memory(memory_id:str,body:MemoryRequest):
        return agent.memory.update(body.user_id,memory_id,body.candidate.model_dump(),body.explicit_consent)
    @api.delete('/memory/{memory_id}')
    def delete(memory_id: str, user_id: str=Query(min_length=1,max_length=80), explicit_consent: bool=False):
        return agent.delete_memory(user_id,memory_id,explicit_consent)
    @api.post('/feedback')
    def feedback(body: FeedbackRequest):
        with agent.sessions.lock:
            return {'candidate':agent.log_feedback(body.user_id,body.session_id,body.feedback),'persisted':False}
    @api.post('/realtime/connect')
    def realtime(body: RoutineRequest):
        agent.sessions.get(body.session_id)
        provider = BrowserVoiceFallback() if settings.voice_provider=='browser' else QwenRealtimePlaceholder()
        return provider.connect(body.session_id)
    return api
