"""Short-lived local vision permissions and numerical evidence for one browser session."""
from collections import OrderedDict
from dataclasses import dataclass, field
from uuid import uuid4

from app.schemas.models import Session, Stage

FRAME_MAX_AGE = 30
PERMIT_TTL = 900


@dataclass
class Permit:
    permit_id: str
    expires_at: float
    used: bool = False


@dataclass
class VisionState:
    session: Session
    media_epoch: int
    permits: dict[str, Permit] = field(default_factory=dict)
    seen: OrderedDict[str, float] = field(default_factory=OrderedDict)
    baseline: dict | None = None
    baseline_version: int = 0
    observation_scope: str | None = None
    pending: tuple[str, str] | None = None
    pending_baseline: bool = False


class LocalVisionSessions:
    """Mutations run under SessionStore.lock, including the revocation callback."""

    def __init__(self, sessions):
        self.sessions = sessions
        self.states: dict[str, VisionState] = {}

    @staticmethod
    def clear_observation(state):
        session = state.session
        if session.visual_state and session.visual_state.get('task') == 'local_region_measurement':
            session.visual_state = None
            session.confidence = 0
        state.observation_scope = None

    def clear_baseline(self, state):
        state.baseline_version += 1
        state.baseline = None
        if state.pending_baseline:
            state.pending = None
            state.pending_baseline = False
        observation = state.session.visual_state
        if observation and observation.get('task') == 'local_region_measurement':
            if observation.get('comparison') or observation.get('baseline_saved'):
                self.clear_observation(state)

    def drop(self, session):
        state = self.states.pop(session.session_id, None)
        if state:
            self.clear_observation(state)

    def revoke_scope(self, state, scope):
        scopes = {'camera', 'adaptive'} if scope == 'camera' else {scope}
        for name in scopes:
            state.permits.pop(name, None)
        if 'camera' in scopes:
            self.clear_baseline(state)
        if state.pending and state.pending[0] in scopes:
            state.pending = None
            state.pending_baseline = False
        if state.observation_scope in scopes:
            self.clear_observation(state)

    def expire(self, now):
        for sid, state in list(self.states.items()):
            session = state.session
            if self.sessions.sessions.get(sid) is not session or session.media_epoch != state.media_epoch:
                self.drop(session)
                continue
            for scope, permit in list(state.permits.items()):
                if now >= permit.expires_at:
                    self.revoke_scope(state, scope)
            observation = session.visual_state
            if state.baseline and now >= state.baseline['expires_at']:
                self.clear_baseline(state)
            if observation and now - observation.get('captured_at', 0) > FRAME_MAX_AGE:
                self.clear_observation(state)
            if not state.permits:
                self.drop(session)

    def grant(self, session, scope, now):
        self.expire(now)
        if session.stage == Stage.COMPLETE:
            raise PermissionError('Session is finished; start a new session before allowing local checks.')
        state = self.states.get(session.session_id)
        if scope == 'adaptive' and (state is None or 'camera' not in state.permits):
            raise PermissionError('Allow local single-frame checks before adaptive checks.')
        if state is None:
            state = VisionState(session, session.media_epoch)
            self.states[session.session_id] = state
        self.revoke_scope(state, scope)
        expires_at = now + PERMIT_TTL
        if scope == 'adaptive':
            expires_at = min(expires_at, state.permits['camera'].expires_at)
        permit = Permit(str(uuid4()), expires_at)
        state.permits[scope] = permit
        return permit, state.baseline_version

    def begin(self, session, scope, permit_id, frame_id, captured_at, baseline_consent,
              compare_baseline, baseline_version, now):
        self.expire(now)
        state = self.states.get(session.session_id)
        permit = state.permits.get(scope) if state else None
        if not permit or permit.permit_id != permit_id or permit.used:
            raise PermissionError('Allow this type of local check again before sending a frame.')
        if (baseline_consent or compare_baseline) and state.baseline_version != baseline_version:
            raise ValueError('Baseline authorization changed; choose a new baseline.')
        if not now - FRAME_MAX_AGE <= captured_at <= now + 5:
            raise ValueError('Frame is stale; capture again.')
        if frame_id in state.seen:
            raise ValueError('Capture a new frame for recheck.')
        while state.seen and now - next(iter(state.seen.values())) > FRAME_MAX_AGE + 5:
            state.seen.popitem(last=False)
        if len(state.seen) >= 512:
            raise ValueError('Too many local frames; wait before rechecking.')
        state.seen[frame_id] = now
        if scope == 'photo':
            permit.used = True
        self.clear_observation(state)
        token = str(uuid4())
        state.pending = (scope, token)
        previous = state.baseline if compare_baseline and not baseline_consent else None
        state.pending_baseline = baseline_consent or previous is not None
        return state, token, previous

    def publish(self, state, scope, token, observation, measurement, baseline_consent, now):
        self.expire(now)
        session = state.session
        if self.states.get(session.session_id) is not state or state.pending != (scope, token):
            raise ValueError('Local check cancelled; capture again after consent.')
        state.pending = None
        state.pending_baseline = False
        if now - observation['captured_at'] > FRAME_MAX_AGE:
            raise ValueError('Frame expired during the check; capture again.')
        if baseline_consent and measurement:
            state.baseline = {'measurement': measurement, 'expires_at': now + PERMIT_TTL,
                              'frame_id': observation['frame_id']}
            observation['baseline_saved'] = True
        state.observation_scope = scope
        session.visual_state = observation
        session.confidence = 0
