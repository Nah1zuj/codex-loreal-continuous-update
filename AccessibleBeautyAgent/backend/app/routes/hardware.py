"""Thin owner-scoped HTTP bridge. No new intelligence or media pipeline."""
from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal
import time
from trace_hardware.core import Gateway, Event, Simulator

class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid')
class Pairing(Strict):
    session_id:str=Field(min_length=1,max_length=100)
class Pair(Strict):
    code:str=Field(min_length=1,max_length=100)
    name:str=Field(min_length=1,max_length=60)
    capabilities:list[Literal['display','camera','audio_input','audio_output','lighting','haptic','buttons']]=Field(max_length=7)
class DeviceEvent(Strict):
    device_id:str=Field(max_length=100)
    session_id:str=Field(max_length=100)
    timestamp:float
    event_type:Literal['device.connected','device.disconnected','camera.frame_available','camera.capture_failed','audio.input_started','audio.input_stopped','audio.output_started','audio.output_finished','lighting.state_changed','button.pressed']
    payload:dict=Field(default_factory=dict)
    permission_status:Literal['granted','denied']
    sequence:int=Field(ge=1)
class EventEnvelope(Strict):
    event:DeviceEvent
class SimCommand(Strict):
    operation:Literal['connect','disconnect','display','lighting','audio','camera','button']
    consent:bool=False
    brightness:int=Field(default=50,ge=0,le=100)
    temperature:int=Field(default=4000,ge=2700,le=6500)
    audio_type:Literal['audio.input_started','audio.input_stopped','audio.output_started','audio.output_finished']='audio.input_started'
    button:Literal['repeat','stop']='repeat'

def transport(request:Request):
    # Never trust forwarded headers. Remote deployments terminate trusted TLS
    # before this app or run HTTPS directly; no arbitrary endpoint forwarding.
    if request.url.scheme!='https' and request.url.hostname not in ('127.0.0.1','localhost','::1','testserver'):
        raise PermissionError('Hardware requires HTTPS except loopback development')
    if request.headers.get('content-length','0').isdigit() and int(request.headers.get('content-length','0'))>4096:
        raise ValueError('Hardware payload too large; frames/audio are not accepted')

def build_hardware_router(agent):
    router=APIRouter(prefix='/api/hardware',dependencies=[Depends(transport)])
    gateway=Gateway();simulators={}
    def owner(request):return request.state.principal_prefix
    def owned_session(prefix,sid):
        s=agent.sessions.get(sid)
        if not s.user_id.startswith(prefix):raise PermissionError('Session ownership required')
        return s
    def device(request):
        header=request.headers.get('authorization','')
        if not header.startswith('Bearer '):raise PermissionError('Device token required')
        d=gateway.authorize(header[7:]);owned_session(d.owner,d.session_id);return d,header[7:]
    @router.get('/devices')
    def devices(request:Request):return {'devices':gateway.list(owner(request)),'audit':gateway.audit(owner(request)),'prototype':True}
    @router.post('/pairing')
    def pairing(body:Pairing,request:Request):
        owned_session(owner(request),body.session_id)
        return {'code':gateway.issue(owner(request),body.session_id),'expires_in':120,'grants':['display'],'lease_seconds':1800}
    @router.post('/pair')
    def pair(body:Pair):
        d,token=gateway.pair(body.code,body.name,body.capabilities)
        return {'device':d.status(),'token':token,'prototype':True}
    @router.delete('/devices/{device_id}')
    def remove(device_id:str,request:Request):
        gateway.revoke(owner(request),device_id);return {'disconnected':True}
    @router.get('/display')
    def display(request:Request):
        d,_=device(request);s=owned_session(d.owner,d.session_id);plan=s.makeup_plan
        step=plan.steps[plan.active_index] if plan and 0<=plan.active_index<len(plan.steps) else None
        # No raw transcript, face frames, identity, private memory or model keys.
        return {'device':d.status(),'session_id':d.session_id,'workflow':plan.workflow if plan else s.stage.value,
                'step':{'title':step.title,'instruction':' '.join(step.instructions),'review_status':step.review_status} if step else None,
                'progress':{'completed':sum(x.status=='completed' for x in plan.steps),'total':len(plan.steps)} if plan else None,
                'illustration_only':True}
    @router.post('/events')
    def event(body:EventEnvelope,request:Request):
        _,token=device(request);return gateway.accept(token,Event(**body.event.model_dump()))
    @router.post('/disconnect')
    def disconnect(request:Request):
        d,_=device(request);gateway.revoke(d.owner,d.id);return {'disconnected':True}
    @router.post('/simulator')
    def simulator(body:SimCommand,request:Request):
        key=owner(request)
        # Per-browser bounded, no persistence or actual hardware calls.
        now=time.monotonic()
        for stale,(_,stamp) in list(simulators.items()):
            if now-stamp>900:simulators.pop(stale,None)
        if key not in simulators:
            if len(simulators)>=100:raise ValueError('Simulator capacity reached; restart clears RAM')
            simulators[key]=(Simulator(),now)
        sim=simulators[key][0];simulators[key]=(sim,now)
        if body.operation=='connect':sim.connect();result=sim.get_status()
        elif body.operation=='disconnect':sim.disconnect();result=sim.get_status()
        elif body.operation=='lighting':result=sim.set_lighting(body.brightness,body.temperature,body.consent)
        elif body.operation=='audio':result=sim.audio_event(body.audio_type)
        elif body.operation=='camera':result=sim.camera_state()
        elif body.operation=='button':result=sim.button_event(body.button)
        else:result=sim.display({'title':'TRACE SIMULATOR','instruction':'Deterministic display fixture; no real conversation or analysis.'})
        return {'status':sim.get_status(),'result':result,'simulated':True,'physical_device_changed':False}
    return router
