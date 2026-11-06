import uuid
import time
from threading import RLock
from app.schemas.models import Session, Stage

# Explicit legal state transitions. Consent and tool events use this service.
TRANSITIONS = {
    Stage.INIT:{Stage.ONBOARDING},
    Stage.ONBOARDING:{Stage.INTENT},
    Stage.INTENT:{Stage.CLARIFY,Stage.LOOK_SELECTED},
    Stage.CLARIFY:{Stage.CLARIFY,Stage.LOOK_SELECTED},
    Stage.LOOK_SELECTED:{Stage.MEMORY_CONSENT,Stage.GUIDE,Stage.CHECK_REQUESTED,Stage.INTENT},
    Stage.GUIDE:{Stage.MEMORY_CONSENT,Stage.GUIDE,Stage.CHECK_REQUESTED,Stage.FEEDBACK},
    Stage.CHECK_REQUESTED:{Stage.CAMERA_CONSENT},
    Stage.CAMERA_CONSENT:{Stage.VISION_GATE,Stage.GUIDE,Stage.LOOK_SELECTED},
    Stage.VISION_GATE:{Stage.VISION_CHECK,Stage.VERIFY,Stage.CAMERA_CONSENT,Stage.GUIDE,Stage.LOOK_SELECTED},
    Stage.VISION_CHECK:{Stage.VERIFY,Stage.CAMERA_CONSENT,Stage.GUIDE,Stage.LOOK_SELECTED},
    Stage.VERIFY:{Stage.MEMORY_CONSENT,Stage.GUIDE,Stage.CHECK_REQUESTED,Stage.FEEDBACK,Stage.LOOK_SELECTED},
    Stage.FEEDBACK:{Stage.MEMORY_CONSENT,Stage.FEEDBACK},
    Stage.MEMORY_CONSENT:{Stage.MEMORY_CONSENT,Stage.FEEDBACK},
    Stage.COMPLETE:set(),
}

class SessionStore:
    def __init__(self):
        self.sessions = {}
        self.lock = RLock()
        self.touched={}
    def create(self, user_id='demo'):
        # No durable transcript without review; expire abandoned sessions in RAM.
        with self.lock:
            now=time.monotonic()
            for sid,stamp in list(self.touched.items()):
                if now-stamp>7200:self.sessions.pop(sid,None);self.touched.pop(sid,None)
            while len(self.sessions)>=200:
                sid=min(self.sessions,key=lambda key:self.touched.get(key,0));self.sessions.pop(sid);self.touched.pop(sid,None)
            session = Session(session_id=str(uuid.uuid4()),user_id=user_id)
            self.sessions[session.session_id]=session
            self.touched[session.session_id]=now
            self.transition(session,Stage.ONBOARDING)
            self.transition(session,Stage.INTENT)
            return session
    def get(self, sid):
        with self.lock:
            if sid in self.touched and time.monotonic()-self.touched[sid]>7200:
                self.sessions.pop(sid,None);self.touched.pop(sid,None)
            if sid not in self.sessions:
                row=None
                if getattr(self,'memory',None):
                    with self.memory.connect() as db:
                        row=db.execute('SELECT user_id,locale,payload FROM makeup_sessions WHERE session_id=? AND updated_at>?',(sid,time.time()-30*86400)).fetchone()
                if not row:raise KeyError('Session not found')
                from app.schemas.makeup import MakeupPlan
                import json
                plan=MakeupPlan.model_validate(json.loads(row[2]))
                self.sessions[sid]=Session(session_id=sid,user_id=row[0],locale=row[1],makeup_plan=plan,stage=Stage.INTENT)
                restored=self.sessions[sid]
                restored.stage=Stage.FEEDBACK if plan.status=='completed' else Stage.GUIDE if plan.status=='active' else Stage.LOOK_SELECTED
                restored.routine_step=plan.active_index;restored.routine_total_steps=len(plan.steps);restored.routine_started=plan.status!='draft';restored.scene=plan.occasion
            self.touched[sid]=time.monotonic()
            return self.sessions[sid]
    def transition(self, session, target):
        if target != Stage.COMPLETE and target not in TRANSITIONS[session.stage]:
            raise ValueError(f'Illegal transition {session.stage.value} -> {target.value}')
        session.stage = target
        session.stage_history.append(target.value)
    def stop(self, session):
        session.camera_consent=False
        self.transition(session,Stage.COMPLETE)
