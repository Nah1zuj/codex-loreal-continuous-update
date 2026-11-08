import asyncio
import time
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Request
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field, StrictBool
from starlette.responses import JSONResponse

from app.vision.gate import decode_image
from app.vision.local_regions import LocalRegionAnalyzer
from app.vision.local_session import LocalVisionSessions

Scope = Literal['camera', 'adaptive', 'photo']


class LocalPermit(BaseModel):
    model_config = ConfigDict(extra='forbid')
    session_id: str
    scope: Scope


class LocalFrame(BaseModel):
    model_config = ConfigDict(extra='forbid')
    session_id: str
    permit_id: str | None = Field(default=None, max_length=80)
    capture_kind: Literal['camera', 'photo'] = 'camera'
    adaptive: StrictBool = False
    image: str = Field(max_length=3_000_000)
    frame_id: str = Field(min_length=1, max_length=80)
    captured_at: float = Field(allow_inf_nan=False)
    explicit_consent: StrictBool = False
    baseline_consent: StrictBool = False
    compare_baseline: StrictBool = False
    baseline_version: int | None = Field(default=None, ge=0)
    target: Literal['auto', 'blush', 'lips'] = 'auto'
    locale: Literal['zh-CN', 'en'] | None = None


class LocalRevoke(BaseModel):
    model_config = ConfigDict(extra='forbid')
    permit_id: str | None = Field(default=None, max_length=80)
    baseline: StrictBool = False


class PrivateFrameRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def handle(request: Request):
            try:
                return await handler(request)
            except RequestValidationError:
                # The generic validation response echoes its input.
                return JSONResponse({'detail': 'Invalid local visual request.'}, status_code=422)

        return handle


def describe_photo(result):
    # Selected files may be mirrored. Only describe image coordinates.
    result['comparison'] = None
    result['status'] = 'UNCERTAIN'
    result['assessment'] = {'status': 'uncertain', 'scope': 'uploaded_photo_orientation_unknown'}
    regions = {'left_cheek': 'image_right_cheek', 'right_cheek': 'image_left_cheek'}
    result['regions'] = {regions.get(key, key): value for key, value in result.get('regions', {}).items()}
    if result['gate'].get('gate_pass'):
        if result.get('source') == 'local_opencv_proxy':
            result['message'] = '本地关键点模型不可用，仅提供画面质量和区域代理数值。'
            result['message_en'] = 'The local landmark model is unavailable; only image quality and coarse color values are reported. '
        else:
            result['message'] = '已检查图片中的面部定位与局部颜色。'
            result['message_en'] = 'Face position and local colors were inspected. '
        result['message'] += '照片方向未知，只标注图像坐标。'
        result['message_en'] += 'The photo orientation is unknown; any side labels refer to image coordinates.'


def build_local_vision_router(agent):
    router = APIRouter(prefix='/api/vision/local', route_class=PrivateFrameRoute)
    analyzer = LocalRegionAnalyzer(agent.vision.gate)
    local = LocalVisionSessions(agent.sessions)
    agent.sessions.on_media_revoked = local.drop
    sweeper = None

    async def sweep():
        while True:
            await asyncio.sleep(5)
            with agent.sessions.lock:
                local.expire(time.time())

    async def start_sweep():
        nonlocal sweeper
        sweeper = asyncio.create_task(sweep())

    async def stop_sweep():
        if sweeper:
            sweeper.cancel()
            try:
                await sweeper
            except asyncio.CancelledError:
                pass

    router.add_event_handler('startup', start_sweep)
    router.add_event_handler('shutdown', stop_sweep)
    router.add_event_handler('shutdown', analyzer.landmarks.close)

    @router.post('/permits')
    def authorize(body: LocalPermit):
        with agent.sessions.lock:
            session = agent.sessions.get(body.session_id)
            permit, baseline_version = local.grant(session, body.scope, time.time())
            return {'permit_id': permit.permit_id, 'expires_at': permit.expires_at,
                    'scope': body.scope, 'baseline_version': baseline_version}

    @router.post('')
    def observe(body: LocalFrame):
        if body.explicit_consent is not True:
            raise PermissionError('Local frame analysis requires consent.')
        scope = 'photo' if body.capture_kind == 'photo' else 'adaptive' if body.adaptive else 'camera'
        if (scope == 'photo' and (body.adaptive or body.compare_baseline)) or (body.baseline_consent and scope != 'camera'):
            raise ValueError('Only a manual camera frame can establish a baseline.')
        with agent.sessions.lock:
            session = agent.sessions.get(body.session_id)
            target = body.target
            if target == 'auto':
                step = agent.current_step(session) or {}
                target = 'lips' if step.get('visual_task') == 'lip_presence' else 'blush'
            locale = body.locale or session.locale
            state, token, baseline = local.begin(
                session, scope, body.permit_id, body.frame_id, body.captured_at, body.baseline_consent,
                body.compare_baseline, body.baseline_version, time.time(),
            )

        result = analyzer.analyze(decode_image(body.image), baseline['measurement'] if baseline else None, target)
        measurement = result.pop('measurement')
        if scope == 'photo':
            describe_photo(result)
        elif baseline and result.get('comparison'):
            result['comparison']['baseline_frame_id'] = baseline['frame_id']
        observation = {
            'task': 'local_region_measurement', **result,
            'capture_kind': body.capture_kind,
            'orientation': 'unknown' if scope == 'photo' else 'unmirrored',
            'frame_id': body.frame_id, 'captured_at': body.captured_at,
            'observation_id': str(uuid4()), 'target': target, 'baseline_saved': False,
        }
        reviewed = [row for row in agent.coaching.knowledge(locale) if target in row.get('tags', [])]
        observation['knowledge'] = {
            'reviewed_available': bool(reviewed),
            'source_ids': [row['guidance_id'] for row in reviewed[:3]],
            'guidance_status': 'reviewed' if reviewed else 'unavailable',
        }
        message = result['message'] if locale == 'zh-CN' else result['message_en']
        with agent.sessions.lock:
            local.publish(state, scope, token, observation, measurement, body.baseline_consent, time.time())
            return {**agent.respond(session, message, remember=False), 'observation': observation,
                    'provider': observation['source'], 'frame_saved': False}

    @router.get('/{session_id}')
    def observations(session_id: str):
        with agent.sessions.lock:
            session = agent.sessions.get(session_id)
            local.expire(time.time())
            state = local.states.get(session_id)
            latest = session.visual_state if state and state.observation_scope else None
            return {'observations': [latest] if latest and latest.get('task') == 'local_region_measurement' else [],
                    'baseline_available': bool(state and state.baseline), 'images_saved': False}

    @router.delete('/{session_id}')
    def clear(session_id: str, body: LocalRevoke | None = None):
        permit_id = body.permit_id if body else None
        baseline = body.baseline if body else False
        with agent.sessions.lock:
            session = agent.sessions.get(session_id)
            local.expire(time.time())
            state = local.states.get(session_id)
            if state:
                if baseline:
                    permit = state.permits.get('camera')
                    if not permit or permit.permit_id != permit_id:
                        raise PermissionError('Allow local single-frame checks before clearing a baseline.')
                    local.clear_baseline(state)
                    return {'cleared': True, 'baseline_version': state.baseline_version}
                elif permit_id:
                    scope = next((scope for scope, permit in state.permits.items() if permit.permit_id == permit_id), None)
                    if scope:
                        local.revoke_scope(state, scope)
                else:
                    local.drop(session)
            if baseline:
                raise PermissionError('No local camera authorization is active.')
        return {'cleared': True}

    return router
