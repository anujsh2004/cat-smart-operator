from pydantic import BaseModel

from app.schemas.common import EventType, ModuleCategory, ModuleFormat, Priority, TrainingStatus


class Module(BaseModel):
    module_id: str
    title: str
    category: ModuleCategory
    format: ModuleFormat
    duration_min: int
    description: str
    content_url: str | None = None
    # An anomaly_type or event_type (e.g. seatbelt_unfastened); EventType covers both sets
    trigger_anomaly_type: EventType | None = None


class Recommendation(BaseModel):
    module: Module
    reason: str
    priority: Priority


class TrainingProgress(BaseModel):
    module_id: str
    status: TrainingStatus
    progress_pct: int
    score: float | None = None


class TrainingProgressCreate(BaseModel):
    operator_id: str
    module_id: str
    progress_pct: int
    score: float | None = None


class QuizQuestion(BaseModel):
    id: str
    prompt: str
    options: list[str]
    answer_index: int
    explanation: str


class Quiz(BaseModel):
    questions: list[QuizQuestion]
