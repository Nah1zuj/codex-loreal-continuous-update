"""RAM-only pairing, least-privilege leases, bounded audit, deterministic adapters."""
from dataclasses import dataclass, field
from collections import deque
from threading import RLock
from typing import Protocol, Literal
import hashlib
import secrets
import time
import math

Capability=Literal['display','camera','audio_input','audio_output','lighting','haptic','buttons']
ConnectionState=Literal['disconnected','connecting','connected','error']

class Adapter(Protocol):
    id: str
    name: str
    type: str
    capabilities: tuple[Capability,...]
    connection_state: ConnectionState
    def connect(self)->None: ...
    def disconnect(self)->None: ...
    def get_status(self)->dict: ...

class CameraInput(Protocol):
    def camera_state(self)->dict: ...
class DisplayOutput(Protocol):
    def display(self, message:dict)->dict: ...
class LightingControl(Protocol):
    def set_lighting(self, brightness:int, temperature:int, consent:bool)->dict: ...
class AudioEvents(Protocol):
    def audio_event(self, event_type:str)->dict: ...
class AssistiveInput(Protocol):
    def button_event(self, action:Literal['repeat','stop'])->dict: ...
class HapticOutput(Protocol):
    def pulse(self, pattern:Literal['step','stop'], consent:bool)->dict: ...

@dataclass(frozen=True)
class Event:
    device_id:str
    session_id:str
    timestamp:float
    event_type:str
    payload:dict
    permission_status:Literal['granted','denied']
    sequence:int

@dataclass
class Device:
    id:str
    name:str
    type:str
    capabilities:tuple[Capability,...]
    owner:str
    session_id:str
    token_hash:str=field(repr=False)
    expires:float=0
    heartbeat:float=0
    sequence:int=0
    connection_state:ConnectionState='connected'
    def status(self):
        return {k:getattr(self,k) for k in ('id','name','type','capabilities','connection_state','expires')}

class Gateway:
    def __init__(self, clock=time.time):
        self.clock=clock;self.lock=RLock();self.codes={};self.devices={};self.records=deque(maxlen=200)
    def _log(self,owner,device,event):
        self.records.append({'owner':owner,'device_id':device,'timestamp':self.clock(),'event_type':event})
    def _prune(self):
        now=self.clock()
        self.codes={k:v for k,v in self.codes.items() if v[2]>now}
        for d in self.devices.values():
            if now>=d.expires or now-d.heartbeat>300:d.connection_state='disconnected'
        self.devices={k:d for k,d in self.devices.items() if d.expires+900>now}
    def issue(self, owner:str, session_id:str):
        with self.lock:
            self._prune()
            if sum(v[0]==owner for v in self.codes.values())>=3 or len(self.codes)>=100:
                raise ValueError('Pairing limit reached; wait for expiry')
            code=secrets.token_urlsafe(12)
            self.codes[hashlib.sha256(code.encode()).hexdigest()]=(owner,session_id,self.clock()+120)
            self._log(owner,None,'pairing.requested');return code
    def pair(self,code:str,name:str,capabilities:list):
        with self.lock:
            self._prune()
            if not isinstance(code,str) or len(code)>100:raise PermissionError('Invalid pairing code')
            binding=self.codes.pop(hashlib.sha256(code.encode()).hexdigest(),None)
            if not binding:raise PermissionError('Pairing code invalid or expired')
            if len(self.devices)>=100:raise ValueError('Device capacity reached')
            if not isinstance(name,str) or not 1<=len(name.strip())<=60:raise ValueError('Device name required, up to 60 characters')
            if 'display' not in capabilities:raise ValueError('Reference client supports display only')
            token=secrets.token_urlsafe(32);now=self.clock()
            d=Device(secrets.token_hex(12),name.strip(),'browser_mirror',('display',),binding[0],binding[1],hashlib.sha256(token.encode()).hexdigest(),now+1800,now)
            self.devices[d.id]=d;self._log(d.owner,d.id,'device.connected');return d,token
    def authorize(self,token:str):
        with self.lock:
            self._prune()
            if not token or len(token)>200:raise PermissionError('Device authentication required')
            digest=hashlib.sha256(token.encode()).hexdigest()
            d=next((d for d in self.devices.values() if secrets.compare_digest(d.token_hash,digest)),None)
            if not d or d.connection_state!='connected':raise PermissionError('Device disconnected, revoked or expired; pair again')
            d.heartbeat=self.clock();return d
    def list(self,owner):
        with self.lock:
            self._prune();return [d.status() for d in self.devices.values() if d.owner==owner]
    def revoke(self,owner,device_id):
        with self.lock:
            d=self.devices.get(device_id)
            if not d or d.owner!=owner:raise PermissionError('Device ownership required')
            d.connection_state='disconnected';d.token_hash='';self._log(owner,d.id,'device.disconnected')
    def audit(self,owner):
        with self.lock:
            return [{k:v for k,v in r.items() if k!='owner'} for r in self.records if r['owner']==owner and self.clock()-r['timestamp']<86400]
    def accept(self,token,event:Event):
        with self.lock:
            d=self.authorize(token)
            if event.device_id!=d.id or event.session_id!=d.session_id:raise PermissionError('Device/session binding mismatch')
            if event.permission_status!='granted':raise PermissionError('Permission denied')
            if not isinstance(event.timestamp,(float,int)) or not math.isfinite(event.timestamp) or abs(self.clock()-event.timestamp)>30:raise ValueError('Stale event')
            if type(event.sequence)!=int or event.sequence<=d.sequence:raise ValueError('Replayed event')
            # Display reference devices cannot transmit frames, sound, lighting commands
            # or invoke agent tools. New adapters require explicit server-side grants.
            if event.event_type not in ('device.connected','device.disconnected'):raise PermissionError('Capability not granted')
            if event.payload!={}:raise ValueError('Unexpected payload')
            d.sequence=event.sequence;self._log(d.owner,d.id,event.event_type)
            if event.event_type=='device.disconnected':self.revoke(d.owner,d.id)
            return {'accepted':True,'invoked_agent':False}

class UnsupportedAdapter:
    """Contract boundary; never pretend a proprietary device is connected."""
    def __init__(self,kind):
        self.id='unconfigured-'+kind;self.name=kind;self.type=kind
        self.capabilities=();self.connection_state='disconnected'
    def connect(self):raise NotImplementedError('Requires actual authorized endpoint, device and SDK')
    def disconnect(self):self.connection_state='disconnected'
    def get_status(self):return {'id':self.id,'type':self.type,'connection_state':self.connection_state,'capabilities':self.capabilities,'validated':False}

class Simulator:
    id='SIMULATOR-01';name='TRACE simulator';type='simulator'
    capabilities=('display','lighting','audio_input','audio_output','camera','buttons')
    def __init__(self):
        self.connection_state='disconnected';self.brightness=50;self.temperature=4000;self.message={};self.sequence=0
    def connect(self):self.connection_state='connected'
    def disconnect(self):self.connection_state='disconnected';self.message={}
    def get_status(self):
        return {'id':self.id,'name':self.name,'type':self.type,'capabilities':self.capabilities,'connection_state':self.connection_state,'simulated':True,'brightness':self.brightness,'temperature':self.temperature,'sequence':self.sequence}
    def _connected(self):
        if self.connection_state!='connected':raise PermissionError('Simulator is disconnected')
        self.sequence+=1
    def set_lighting(self,brightness,temperature,consent):
        if consent is not True:raise PermissionError('Explicit simulator command consent required')
        if type(brightness)!=int or type(temperature)!=int or not 0<=brightness<=100 or not 2700<=temperature<=6500:raise ValueError('Lighting outside allowed bounds')
        self._connected();self.brightness=brightness;self.temperature=temperature
        return {**self.get_status(),'verified':True,'physical_device_changed':False}
    def display(self,message):
        self._connected()
        if set(message)-{'title','instruction'} or any(not isinstance(v,str) or len(v)>2000 for v in message.values()):raise ValueError('Invalid display message')
        self.message=dict(message);return {'simulated':True,'display':self.message}
    def camera_state(self):return {'simulated':True,'capture':'unsupported','frames_processed':0}
    def audio_event(self,event_type):
        self._connected()
        if event_type not in ('audio.input_started','audio.input_stopped','audio.output_started','audio.output_finished'):raise ValueError('Invalid audio event')
        return {'simulated':True,'event_type':event_type,'sequence':self.sequence,'audio_recorded':False}
    def button_event(self,action):
        self._connected()
        if action not in ('repeat','stop'):raise ValueError('Unsupported button')
        return {'simulated':True,'event_type':'button.pressed','action':action,'invoked_agent':False}
