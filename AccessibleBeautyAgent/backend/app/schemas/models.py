from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field, StrictBool, model_validator

from app.schemas.full_look import FullLook,ExperienceMode,SectionName
from app.schemas.makeup import MakeupPlan

class Stage(str, Enum):
    INIT='INIT'
    ONBOARDING='ONBOARDING'
    INTENT='INTENT'
    CLARIFY='CLARIFY'
    LOOK_SELECTED='LOOK_SELECTED'
    GUIDE='GUIDE'
    CHECK_REQUESTED='CHECK_REQUESTED'
    CAMERA_CONSENT='CAMERA_CONSENT'
    VISION_GATE='VISION_GATE'
    VISION_CHECK='VISION_CHECK'
    VERIFY='VERIFY'
    FEEDBACK='FEEDBACK'
    MEMORY_CONSENT='MEMORY_CONSENT'
    COMPLETE='COMPLETE'

class Session(BaseModel):
    makeup_plan: MakeupPlan | None = None
    session_id: str
    user_id: str = 'demo'
    locale: Literal['zh-CN','en'] = 'zh-CN'
    experience_mode: ExperienceMode | None = None
    todays_look: FullLook | None = None
    mood: list[str] = Field(default_factory=list)
    formality: str | None = None
    stage: Stage = Stage.INIT
    scene: str | None = None
    desired_impression: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    preference_refs: list[str] = Field(default_factory=list)
    selected_look: str | None = None
    selected_products: list[dict] = Field(default_factory=list)
    routine_id: str | None = None
    routine_step: int = 0
    routine_total_steps: int = 0
    routine_started: bool = False
    camera_consent: bool = False
    media_epoch: int = Field(default=0, exclude=True)
    memory_consent: bool = False
    visual_state: dict | None = None
    confidence: float = 0
    last_tool_call: dict | None = None
    tool_calls: list[dict] = Field(default_factory=list)
    rag_documents: list[dict] = Field(default_factory=list)
    memory_candidate: dict | None = None
    last_response: str = ''
    story_context: list[str] = Field(default_factory=list,max_length=10)
    stage_history: list[str] = Field(default_factory=lambda: ['INIT'])

class ChatRequest(BaseModel):
    event_id: str | None = Field(default=None,min_length=1,max_length=80)
    expected_step_id: str | None = Field(default=None,max_length=120)
    expected_plan_id: str | None = Field(default=None,min_length=1,max_length=80)
    expected_revision: int | None = Field(default=None,ge=0)
    locale: Literal['zh-CN','en'] | None = None
    session_id: str | None = None
    user_id: str = Field(default='demo', min_length=1, max_length=80)
    message: str = Field(default='', max_length=4000)
    action: Literal['message', 'camera_consent', 'memory_consent'] = 'message'
    consent: StrictBool | None = None
    experience_mode: ExperienceMode | None = None

class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    filters: dict[str, str] = Field(default_factory=dict)
    limit: int = Field(default=5, ge=1, le=50)

class LookRequest(BaseModel):
    scene: str = 'daily'
    desired_impression: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    preferences: dict = Field(default_factory=dict)

class ProductRequest(BaseModel):
    look_id: str
    scene: str = 'daily'
    preferences: dict = Field(default_factory=dict)

class RoutineRequest(BaseModel):
    session_id: str
    routine_id: str | None = None
    event_id: str | None = Field(default=None,min_length=1,max_length=80)
    expected_step_id: str | None = Field(default=None,max_length=120)
    expected_plan_id: str | None = Field(default=None,min_length=1,max_length=80)
    expected_revision: int | None = Field(default=None,ge=0)

Task = Literal['blush_presence', 'lip_presence']
BlushStatus = Literal['NO_BLUSH', 'LEFT_ONLY', 'RIGHT_ONLY', 'BOTH', 'UNCERTAIN']
LipStatus = Literal['NOT_APPLIED', 'APPLIED', 'OBVIOUS_OVERFLOW', 'UNCERTAIN']

class VisualResult(BaseModel):
    task: Task
    status: str
    left_visible: bool | None = None
    right_visible: bool | None = None
    obvious_difference: bool = False
    image_quality: Literal['good', 'moderate', 'poor'] = 'good'
    confidence: float = Field(ge=0, le=1)
    simulated: bool = False

    @model_validator(mode='after')
    def allowed_status(self):
        statuses = {'NO_BLUSH', 'LEFT_ONLY', 'RIGHT_ONLY', 'BOTH', 'UNCERTAIN'} if self.task == 'blush_presence' else {'NOT_APPLIED', 'APPLIED', 'OBVIOUS_OVERFLOW', 'UNCERTAIN'}
        if self.status not in statuses:
            raise ValueError('Status is not allowed for this visual task')
        if self.task == 'blush_presence':
            self.left_visible = self.status in ('LEFT_ONLY', 'BOTH') if self.status != 'UNCERTAIN' else None
            self.right_visible = self.status in ('RIGHT_ONLY', 'BOTH') if self.status != 'UNCERTAIN' else None
        return self

class VisionRequest(BaseModel):
    model_config = {"extra": "forbid"}
    capture_kind: Literal["photo", "video_sample"] = "photo"
    remote_frame_consent: StrictBool = False
    session_id: str
    task: Task = 'blush_presence'
    images: list[str] = Field(default_factory=list, max_length=3)
    demo: StrictBool = False
    mock_status: str = 'BOTH'

    @model_validator(mode="after")
    def single_video_sample(self):
        if self.capture_kind == "video_sample" and self.demo:
            raise ValueError("Video samples cannot use three-frame demo consensus")
        if self.capture_kind == "video_sample" and len(self.images) != 1:
            raise ValueError("Video analysis requires exactly one sampled image")
        return self

class MemoryCandidate(BaseModel):
    feedback: str = Field(min_length=1, max_length=2000)
    context: str = Field(default='unspecified', max_length=100)
    preferred_finish: list[str] = Field(default_factory=list, max_length=10)
    preferred_saturation: Literal['low', 'medium_low', 'medium', 'high'] | None = None
    avoid: list[str] = Field(default_factory=list, max_length=20)

    material_preferences: list[str] = Field(default_factory=list,max_length=8)
    domain_preferences: dict[SectionName,list[str]] = Field(default_factory=dict,max_length=6)

class MemoryRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=80)
    candidate: MemoryCandidate
    explicit_consent: StrictBool = False

class FeedbackRequest(BaseModel):
    user_id: str = 'demo'
    locale: Literal['zh-CN','en'] = 'zh-CN'
    session_id: str
    feedback: str = Field(min_length=1, max_length=2000)

class Intent(BaseModel):
    scene: str | None = None
    desired_impression: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
