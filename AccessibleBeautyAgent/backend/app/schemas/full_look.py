"""Session-scoped styling plans. Confirmation never implies memory permission."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

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
    selected_suggestion_id: str | None = None
    facts: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
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
    pending_coordination: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def user_confirmed_sections(self) -> list[SectionName]:
        return [key for key, section in self.sections.items() if section.state == 'confirmed']

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
    decision: Literal['select','confirm','skip']
    suggestion_id: str | None = Field(default=None,min_length=1,max_length=120)
    expected_version: int | None = Field(default=None,ge=1)

    @model_validator(mode='after')
    def validate_selection(self):
        if self.decision == 'select' and (len(self.sections) != 1 or self.suggestion_id is None):
            raise ValueError('Select one suggestion in a single domain')
        if self.decision != 'select' and self.suggestion_id is not None:
            raise ValueError('suggestion_id is only used when selecting')
        return self

class PlanMemoryRequest(PlanRequest):
    feedback: str = Field(min_length=1,max_length=2000)

class MaterialQuery(BaseModel):
    model_config = ConfigDict(extra='forbid')
    material_ids: list[str] = Field(min_length=1,max_length=2)

