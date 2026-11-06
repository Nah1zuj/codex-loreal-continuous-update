"""Validated plan data; owner/session identities are always supplied by the server."""
from typing import Literal
from pydantic import BaseModel,Field,ConfigDict,model_validator

class Lesson(BaseModel):
    model_config=ConfigDict(extra='forbid')
    purpose:str=Field(min_length=1,max_length=400)
    requiredProducts:list[str]=Field(min_length=1,max_length=10)
    preparation:list[str]=Field(min_length=1,max_length=10)
    instructions:list[str]=Field(min_length=1,max_length=12)
    accessibilityInstructions:list[str]=Field(min_length=1,max_length=8)
    commonMistakes:list[str]=Field(min_length=1,max_length=8)
    completionCriteria:list[str]=Field(min_length=1,max_length=8)
    optionalVisualCheck:str|None=None

class LessonSource(BaseModel):
    source_id: str
    title: str
    version: int = Field(ge=1)
    url: str | None
    local_file: str | None
    use_permission: Literal['original', 'cc-by', 'cc0', 'licensed']
    use_basis: str


class LessonProvenance(BaseModel):
    version: int = Field(ge=1)
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    sources: list[LessonSource] = Field(min_length=1)


class MakeupStep(Lesson):
    id:str=Field(min_length=1,max_length=120)
    order:int=Field(ge=1,le=30)
    title:str=Field(min_length=1,max_length=100)
    source_id:str
    review_status:str
    lesson_provenance: LessonProvenance | None = None
    status:Literal['pending','active','completed','skipped']='pending'


class LegacyRoutineRef(BaseModel):
    """Pin a stored plan to its catalogue entry, without storing lesson text."""
    model_config = ConfigDict(extra='forbid')
    routine_id: str
    look_id: str
    version: int = Field(ge=1)


class LegacyRoutineStep(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(min_length=1, max_length=120)
    order: int = Field(ge=1)
    title: str
    optionalVisualCheck: str | None = None
    status: Literal['pending', 'active', 'completed', 'skipped'] = 'pending'

class PlanNeeds(BaseModel):
    model_config=ConfigDict(extra='forbid')
    style:Literal['natural','warm','professional','evening','beginner']='natural'
    occasion:str=Field(default='daily',max_length=120)
    aesthetic:str=Field(default='',max_length=400)
    minutes:int=Field(default=15,ge=3,le=120)
    own_products:list[str]=Field(default_factory=list,max_length=20)
    complexity:Literal['simple','standard']='simple'
    accessibility_preferences:list[str]=Field(default_factory=list,max_length=10)
    reference_ids:list[str]=Field(default_factory=list,max_length=3)
    recommendations:bool=False
    avoid: list[str] = Field(default_factory=list, max_length=10)
    clarified_fields: list[Literal['occasion', 'aesthetic', 'minutes', 'own_products', 'avoid']] = Field(
        default_factory=list, max_length=5,
    )

class MakeupPlan(BaseModel):
    model_config=ConfigDict(extra='forbid')
    id:str
    userId:str
    sessionId:str
    name:str
    occasion:str
    styleDescription:str
    estimatedMinutes:int
    needs:PlanNeeds
    steps:list[MakeupStep | LegacyRoutineStep]=Field(min_length=1)
    legacy_routine: LegacyRoutineRef | None = Field(default=None, exclude_if=lambda value: value is None)
    status:Literal['draft','active','completed']='draft'
    workflow:Literal['PLAN_CREATED','READY','WAITING_FOR_USER','PAUSED','SESSION_COMPLETE']='READY'
    active_index:int=Field(default=0,ge=0)
    revision:int=0
    generation_status:Literal['grounded','fallback']='grounded'
    knowledge_status:Literal['reviewed','draft']='draft'
    date:str
    saved_journal_id:str|None=None
    summary_presented:bool=False
    session_ended: bool = Field(default=False, exclude_if=lambda value: not value)
    @model_validator(mode='after')
    def ordered(self):
        if [s.order for s in self.steps]!=list(range(1,len(self.steps)+1)):raise ValueError('Steps must be consecutively ordered')
        if len({s.id for s in self.steps})!=len(self.steps):raise ValueError('Duplicate steps')
        if self.active_index>=len(self.steps):raise ValueError('Active index out of range')
        if self.legacy_routine:
            if not all(isinstance(step, LegacyRoutineStep) for step in self.steps):
                raise ValueError('Legacy plans must contain catalogue step references')
        elif len(self.steps)>30 or not all(isinstance(step, MakeupStep) for step in self.steps):
            raise ValueError('Coaching plans must contain at most 30 validated lessons')
        return self

class PlanProposal(BaseModel):
    """The model selects knowledge IDs; it cannot replace teaching or set progress."""
    model_config=ConfigDict(extra='forbid')
    lesson_ids:list[str]=Field(min_length=1,max_length=20)



class CoachingCommand(BaseModel):
    model_config = ConfigDict(extra='forbid')
    session_id: str = Field(min_length=1, max_length=80)
    event_id: str = Field(min_length=1, max_length=80)
    action: Literal['start', 'advance', 'skip', 'pause', 'resume', 'finish', 'previous']
    expected_plan_id: str = Field(min_length=1, max_length=80)
    expected_revision: int = Field(ge=0)
    expected_step_id: str | None = Field(default=None, min_length=1, max_length=120)
