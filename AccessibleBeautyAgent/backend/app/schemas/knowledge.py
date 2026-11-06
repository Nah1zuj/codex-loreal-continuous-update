"""Canonical Beauty KB schemas. Legacy Phase 1 field names remain accepted.

Vocabulary values live in data/config, not hard-coded attribute enums.
"""
from datetime import datetime
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field, AliasChoices, StrictBool, field_validator, model_validator
from app.schemas.makeup import Lesson

ID = r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,119}$'

class ReviewStatus(str,Enum):
    RAW='RAW'
    DRAFT='DRAFT'
    AI_GENERATED='AI_GENERATED'
    HUMAN_VERIFIED='HUMAN_VERIFIED'
    REJECTED='REJECTED'
    DEPRECATED='DEPRECATED'

class Record(BaseModel):
    model_config={'extra':'forbid','populate_by_name':True}
    source: str = 'unknown'
    source_type: str = 'other'
    source_ids: list[str] = Field(default_factory=list)
    verified: StrictBool = False
    demo_data: StrictBool = False
    status: ReviewStatus = ReviewStatus.DRAFT
    version: int = Field(default=1,ge=1)
    updated_at: datetime | None = None
    review_notes: str = ''
    verified_by: str | None = None
    verified_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    @model_validator(mode='before')
    @classmethod
    def legacy_sample(cls,data):
        data=dict(data)
        if data.get('source_type')=='sample' and 'demo_data' not in data:data['demo_data']=True
        return data

class Attributes(BaseModel):
    model_config={'extra':'forbid'}

class Overall(Attributes):
    intensity: str | None = None
    contrast: str | None = None

class BaseAttributes(Attributes):
    finish: str | None = None
    coverage: str | None = None

class BlushAttributes(Attributes):
    visible: StrictBool | None = None
    intensity: str | None = None
    placement: str | None = None
    finish: str | None = None

class LipAttributes(Attributes):
    visible: StrictBool | None = None
    saturation: str | None = None
    finish: str | None = None

class EyeAttributes(Attributes):
    definition: str | None = None

class ReferenceQuality(Attributes):
    face_visible: StrictBool | None = None
    lighting: str | None = None
    pose: str | None = None

class BeautyLook(Record):
    look_id: str = Field(pattern=ID)
    name: str = Field(min_length=1)
    description: str = ''
    scene: list[str] = Field(default_factory=list,validation_alias=AliasChoices('scene','scenes'))
    desired_impression: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    overall: Overall = Field(default_factory=Overall)
    base: BaseAttributes = Field(default_factory=BaseAttributes)
    blush: BlushAttributes = Field(default_factory=BlushAttributes)
    lip: LipAttributes = Field(default_factory=LipAttributes)
    eye: EyeAttributes = Field(default_factory=EyeAttributes)
    routine_id: str | None = None
    routine_ids: list[str] = Field(default_factory=list)
    reference_ids: list[str] = Field(default_factory=list)
    product_ids: list[str] = Field(default_factory=list)
    @field_validator('base',mode='before')
    @classmethod
    def base_string(cls,value):return {'finish':value} if isinstance(value,str) else value
    @model_validator(mode='after')
    def routine_links(self):
        if 'routine_ids' in self.model_fields_set:
            self.routine_id=self.routine_ids[0] if self.routine_ids else None
        elif self.routine_id:
            self.routine_ids=[self.routine_id]
        return self

class RoutineStep(BaseModel):
    model_config={'extra':'forbid'}
    step_id: str = Field(pattern=ID)
    name: str = ''
    order: int = Field(default=1,ge=1)
    makeup_area: str | None = None
    instruction: str = Field(min_length=1)
    instruction_slow: str = ''
    instruction_repeat: str = ''
    explanation_why: str = ''
    visual_check_required: StrictBool = False
    visual_task: Literal['blush_presence','lip_presence'] | None = None
    success_condition: str = ''
    fallback_instruction: str = ''
    @model_validator(mode='after')
    def fallbacks(self):
        self.name=self.name or self.step_id
        self.instruction_slow=self.instruction_slow or self.instruction
        self.instruction_repeat=self.instruction_repeat or ('重复：'+self.instruction)
        if self.visual_check_required and not self.visual_task:raise ValueError('visual_task is required when visual_check_required=true')
        return self

class BeautyRoutine(Record):
    routine_id: str = Field(pattern=ID)
    look_id: str = Field(pattern=ID)
    name: str = ''
    scene: list[str] = Field(default_factory=list)
    steps: list[RoutineStep] = Field(min_length=1)
    @model_validator(mode='before')
    @classmethod
    def order_legacy_steps(cls,data):
        data=dict(data)
        if isinstance(data.get('steps'),list):data['steps']=[{'order':i+1,**step} for i,step in enumerate(data['steps'])]
        return data
    @model_validator(mode='after')
    def steps_valid(self):
        if len({s.step_id for s in self.steps})!=len(self.steps):raise ValueError('Duplicate step_id')
        if len({s.order for s in self.steps})!=len(self.steps):raise ValueError('Duplicate step order')
        self.steps.sort(key=lambda x:x.order)
        return self

class ReferenceCase(Record):
    reference_id: str = Field(pattern=ID)
    look_id: str = Field(pattern=ID)
    media_type: Literal['image','video_frame']='image'
    source_file: str
    source_id: str | None = None
    frame_timestamp: float | None = Field(default=None,ge=0)
    scene: list[str] = Field(default_factory=list,validation_alias=AliasChoices('scene','scenes'))
    overall: Overall = Field(default_factory=Overall)
    base: BaseAttributes = Field(default_factory=BaseAttributes)
    blush: BlushAttributes = Field(default_factory=BlushAttributes)
    lip: LipAttributes = Field(default_factory=LipAttributes)
    eye: EyeAttributes = Field(default_factory=EyeAttributes)
    quality: ReferenceQuality = Field(default_factory=ReferenceQuality)
    confidence: float | None = Field(default=None,ge=0,le=1)
    uncertainty_notes: str = ''
    notes: str = ''
    ai_generated_draft: StrictBool = False
    human_verified: StrictBool = False
    @model_validator(mode='before')
    @classmethod
    def legacy_fields(cls,data):
        data=dict(data)
        if 'eye_definition' in data:data.setdefault('eye',{'definition':data.pop('eye_definition')})
        if isinstance(data.get('uncertainty_notes'),list):data['uncertainty_notes']='\n'.join(data['uncertainty_notes'])
        return data
    @model_validator(mode='after')
    def review(self):
        if self.source_id and self.source_id not in self.source_ids:self.source_ids.append(self.source_id)
        if self.verified and not self.human_verified:raise ValueError('Reference cannot be verified without human verification')
        if self.human_verified and (not self.verified or not self.verified_by or not self.verified_at):raise ValueError('Human verification requires verified=true, verified_by and verified_at')
        if self.status==ReviewStatus.HUMAN_VERIFIED and not self.human_verified:raise ValueError('HUMAN_VERIFIED status requires human verification')
        return self

class BeautyProduct(Record):
    product_id: str = Field(pattern=ID)
    brand: str = Field(min_length=1)
    name: str = ''
    category: str = Field(min_length=1)
    finish: str | None = None
    saturation: str | None = None
    undertone: str | None = None
    contexts: list[str] = Field(default_factory=list)
    look_ids: list[str] = Field(default_factory=list)
    claims: list[str] = Field(default_factory=list)

class AccessibilityGuidance(Record):
    teaching: Lesson | None = None
    guidance_id: str = Field(pattern=ID,validation_alias=AliasChoices('guidance_id','document_id'))
    category: str = 'voice_instruction'
    principle: str = ''
    description: str = ''
    content: str = ''
    preferred_pattern: str = ''
    avoid_pattern: str = ''
    example_good: str = ''
    example_bad: str = ''
    scene: list[str] = Field(default_factory=list)
    @model_validator(mode='after')
    def text(self):
        self.description=self.description or self.content
        self.content=self.description
        if not self.content:raise ValueError('description/content is required')
        return self

class SourceRecord(Record):
    source_id: str = Field(pattern=ID)
    title: str = Field(min_length=1)
    creator: str | None = None
    url: str | None = None
    local_file: str | None = None
    accessed_at: str | None = None
    notes: str = ''
    @field_validator('url')
    @classmethod
    def valid_url(cls,value):
        if value:
            from urllib.parse import urlsplit
            parsed=urlsplit(value)
            if parsed.scheme not in ('http','https') or not parsed.hostname or any(c.isspace() for c in value):raise ValueError('url must be a valid http/https URL')
        return value

class KnowledgeDocument(BaseModel):
    document_id: str
    document_type: Literal['LOOK','ROUTINE','REFERENCE_CASE','PRODUCT','ACCESSIBILITY_GUIDANCE']
    title: str
    content: str
    source: str
    metadata: dict

MODELS={'LOOK':BeautyLook,'ROUTINE':BeautyRoutine,'REFERENCE_CASE':ReferenceCase,'PRODUCT':BeautyProduct,'ACCESSIBILITY_GUIDANCE':AccessibilityGuidance,'SOURCE':SourceRecord}
FILES={'LOOK':'looks.json','ROUTINE':'routines.json','REFERENCE_CASE':'reference_cases.json','PRODUCT':'products.json','ACCESSIBILITY_GUIDANCE':'accessibility_guidance.json','SOURCE':'sources.json'}
IDS={'LOOK':'look_id','ROUTINE':'routine_id','REFERENCE_CASE':'reference_id','PRODUCT':'product_id','ACCESSIBILITY_GUIDANCE':'guidance_id','SOURCE':'source_id'}
