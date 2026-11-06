import time,uuid,asyncio
from collections import OrderedDict
from typing import Literal
from fastapi import APIRouter
from pydantic import BaseModel,ConfigDict,Field,StrictBool
from app.vision.gate import decode_image
from app.vision.local_regions import LocalRegionAnalyzer

class LocalFrame(BaseModel):
    model_config=ConfigDict(extra='forbid')
    session_id:str
    capture_kind:Literal['camera','photo']='camera'
    image:str=Field(max_length=3_000_000)
    frame_id:str=Field(min_length=1,max_length=80)
    captured_at:float
    explicit_consent:StrictBool=False
    baseline_consent:StrictBool=False
    target:Literal['auto','blush','lips']='auto'
    locale:Literal['zh-CN','en']|None=None

def build_local_vision_router(agent):
    router=APIRouter(prefix='/api/vision')
    analyzer=LocalRegionAnalyzer(agent.vision.gate);measurements=OrderedDict();seen=OrderedDict();history=OrderedDict();epochs=OrderedDict()
    sweeper=None
    def expire():
        now=time.time()
        with agent.sessions.lock:
            for sid in list(history):
                history[sid]=[row for row in history.get(sid,[]) if now-row['captured_at']<900]
                if not history[sid]:history.pop(sid,None)
            for sid,(stamp,_) in list(measurements.items()):
                if now-stamp>=900:measurements.pop(sid,None)
            for session in list(agent.sessions.sessions.values()):
                observation=session.visual_state
                if observation and observation.get('task')=='local_region_measurement' and now-observation.get('captured_at',0)>=900:
                    session.visual_state=None;session.confidence=0
    def invalidate(sid,token):
        epochs[sid]=token;epochs.move_to_end(sid)
        while len(epochs)>200:epochs.popitem(last=False)
    async def sweep():
        while True:
            await asyncio.sleep(30)
            expire()
    async def start_sweep():
        nonlocal sweeper
        sweeper=asyncio.create_task(sweep())
    async def stop_sweep():
        if sweeper:
            sweeper.cancel()
            try:await sweeper
            except asyncio.CancelledError:pass
    router.add_event_handler('startup',start_sweep)
    router.add_event_handler('shutdown',stop_sweep)
    router.add_event_handler('shutdown',analyzer.landmarks.close)
    @router.post('/local')
    def local(body:LocalFrame):
        if body.explicit_consent is not True:raise PermissionError('Local frame analysis requires consent')
        if body.capture_kind=='photo' and body.baseline_consent:raise ValueError('Uploaded photos cannot establish an oriented live-camera baseline')
        s=agent.sessions.get(body.session_id)
        # A failed new request must never leave an older assessment masquerading as fresh.
        request_token=str(uuid.uuid4())
        with agent.sessions.lock:
            media_epoch=s.media_epoch
            s.visual_state=None;s.confidence=0;invalidate(s.session_id,request_token)
        now=time.time()
        if not now-30<=body.captured_at<=now+5:raise ValueError('Frame is stale; capture again')
        token=(s.session_id,body.frame_id)
        if token in seen:raise ValueError('Capture a new frame for recheck')
        seen[token]=now
        while len(seen)>1000 or (seen and now-next(iter(seen.values()))>1800):seen.popitem(last=False)
        expire()
        previous=measurements.get(s.session_id)
        target=body.target
        if target=='auto':
            step=agent.current_step(s) or {}
            target='lips' if step.get('visual_task')=='lip_presence' else 'blush'
        all_rows=[row for row in history.get(s.session_id,[]) if now-row['captured_at']<900]
        rows=[row for row in all_rows if row.get('target')==target]
        recent=next((row['measurement'] for row in reversed(rows) if row.get('measurement')),None)
        result=analyzer.analyze(decode_image(body.image),previous[1] if previous else recent,target)
        measurement=result.pop('measurement')
        if body.capture_kind=='photo':
            # Uploaded photos may be mirrored. Never infer the person's sides or
            # compare an unknown-oriented photo to a live-camera baseline.
            measurement=None;result['comparison']=None;result['status']='UNCERTAIN'
            result['assessment']={'status':'uncertain','scope':'uploaded_photo_orientation_unknown'}
            result['regions']={({'left_cheek':'image_right_cheek','right_cheek':'image_left_cheek'}.get(k,k)):v for k,v in result.get('regions',{}).items()}
            if result['gate'].get('gate_pass'):
                result['message']='已检查图片中的面部定位与局部颜色。照片是否镜像未知，暂不判断你本人左右，也不能确认需要补色。请保持均匀光线，或使用实时摄像头继续检查。'
                result['message_en']='Face geometry and local colors were inspected. Photo orientation is unknown: your physical sides and a need for more makeup cannot be confirmed. Use even light or continue with the live camera.'
        observation={'task':'local_region_measurement',**result,'capture_kind':body.capture_kind,'orientation':'unknown' if body.capture_kind=='photo' else 'unmirrored','frame_id':body.frame_id,'captured_at':body.captured_at,'observation_id':str(uuid.uuid4()),'target':target}
        locale=body.locale or s.locale
        reviewed=[row for row in agent.coaching.knowledge(locale) if ('blush' if target=='blush' else 'lips') in row.get('tags',[])]
        observation['knowledge']={'reviewed_available':bool(reviewed),'source_ids':[row['guidance_id'] for row in reviewed[:3]],'guidance_status':'reviewed' if reviewed else 'unavailable'}
        with agent.sessions.lock:
            if s.media_epoch!=media_epoch or epochs.get(s.session_id)!=request_token:raise ValueError('Local check cancelled; capture again after consent')
            if body.baseline_consent and measurement:
                measurements[s.session_id]=(now,measurement)
                while len(measurements)>200:measurements.popitem(last=False)
            history[s.session_id]=(all_rows+[{'observation':observation,'measurement':measurement,'captured_at':body.captured_at,'target':target}])[-10:]
            while len(history)>200:history.popitem(last=False)
            s.visual_state=observation;s.confidence=0
        message=result['message'] if locale=='zh-CN' else result.get('message_en','Local color measurements are uncalibrated. Makeup coverage cannot be confirmed.')
        # DeepSeek may choose a bounded follow-up, never generate or overwrite visual facts.
        observation['feedback_source']='local_evidence'
        if agent.settings.model_provider=='deepseek' and agent.settings.allow_remote_ai:
            try:
                import json
                from app.services.model_client import RemoteModelClient
                choice=RemoteModelClient(agent.settings,'deepseek').chat_json(agent.settings.deepseek_model,
                    'Select one next_action from recheck, keep, preference, lighting. Return JSON only. Visual facts are authoritative; do not produce new observations or infer traits.',
                    json.dumps({'target':target,'assessment':result.get('assessment'),'warnings':result.get('quality_warnings',[]),'current_step':(agent.current_step(s) or {}).get('name'),'reviewed_knowledge':[{'id':row['guidance_id'],'principle':row['principle'],'description':row['description']} for row in reviewed[:3]]},ensure_ascii=False))
                actions={'recheck':('调整后可以说“再看一次”。','After adjusting, you can say check again.'),
                         'keep':('你也可以保持现在的表达，继续下一步。','You can also keep your expression and continue to the next step.'),
                         'preference':('你更想保留两侧差异，还是让颜色更接近？','Would you prefer to keep the difference or bring the colors closer?'),
                         'lighting':('我们先调整到均匀光线，再取一张新画面。','Let us find even light, then capture a fresh frame.')}
                action=choice.get('next_action');action='lighting' if not result['gate'].get('gate_pass') else 'recheck' if body.capture_kind=='photo' else action
                if action in actions:message+=' '+actions[action][0 if locale=='zh-CN' else 1];observation['feedback_source']='local_evidence_deepseek_bounded_followup'
            except (RuntimeError,PermissionError,ValueError,KeyError,TypeError):observation['feedback_source']='local_evidence_text_fallback'
        if s.media_epoch!=media_epoch or s.visual_state is not observation or epochs.get(s.session_id)!=request_token:raise ValueError('Local check cancelled; no fresh observation available')
        return {**agent.respond(s,message),'observation':s.visual_state,'provider':'local_opencv','frame_saved':False}
    @router.get('/local/{session_id}')
    def observations(session_id:str):
        agent.sessions.get(session_id)
        expire()
        return {'observations':[row['observation'] for row in history.get(session_id,[]) if time.time()-row['captured_at']<900],'images_saved':False}
    @router.delete('/local/{session_id}')
    def clear(session_id:str):
        s=agent.sessions.get(session_id)
        with agent.sessions.lock:
            invalidate(session_id,None);measurements.pop(session_id,None);history.pop(session_id,None)
            s.visual_state=None;s.confidence=0
        return {'cleared':True}
    return router
