"""Session-scoped styling plans. Confirmation never implies memory permission."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

SectionName = Literal['skincare','makeup','hair','outfit','accessories','fragrance']
ExperienceMode = Literal['voice','visual','text']
DOMAINS = ('skincare','makeup','hair','outfit','accessories','fragrance')

class Suggestion(BaseModel):
    id: str
    display_name_zh: str
    display_name_en: str = ''
    reason: str
    source_refs: list[str] = Field(default_factory=list)
    verified_status: str = 'DEMO_CURATED'
    user_override: bool = False
    optional: bool = True

class LookSection(BaseModel):
    state: Literal['proposed','confirmed','skipped'] = 'proposed'
    optional: bool = True
    suggestions: list[Suggestion] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)
    look_id: str | None = None
    routine_id: str | None = None

class FullLook(BaseModel):
    plan_id: str
    session_id: str
    scene: str
    desired_impression: list[str] = Field(default_factory=list)
    review_status: Literal['DEMO_CURATED'] = 'DEMO_CURATED'
    version: int = 1
    sections: dict[SectionName,LookSection]
    source_refs: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    user_confirmed_sections: list[SectionName] = Field(default_factory=list)
    pending_coordination: list[str] = Field(default_factory=list)

class PlanRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    session_id: str = Field(min_length=1,max_length=100)

class RevisionRequest(PlanRequest):
    user_request: str = Field(min_length=1,max_length=2000)
    target_sections: list[SectionName] = Field(default_factory=list,max_length=6)
    constraints: dict[SectionName,str] = Field(default_factory=dict)
    expected_version: int | None = Field(default=None,ge=1)

class ConfirmationRequest(PlanRequest):
    sections: list[SectionName] = Field(min_length=1,max_length=6)
    decision: Literal['confirm','skip']
    expected_version: int | None = Field(default=None,ge=1)

class PlanMemoryRequest(PlanRequest):
    feedback: str = Field(min_length=1,max_length=2000)

class MaterialQuery(BaseModel):
    model_config = ConfigDict(extra='forbid')
    material_ids: list[str] = Field(min_length=1,max_length=2)

