from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class AIAnalysisBase(BaseModel):
    manager_name: str
    script_started_correctly: bool
    asked_vin: bool
    asked_mileage: bool
    offered_diagnostics: bool
    asked_repair_history: bool
    service_booking: bool
    correct_termination: bool
    rude: bool
    conflict: bool
    answered_topic: bool
    toxic: bool
    violations: bool
    needs_attention: bool
    issue_type: str | None
    manager_comment: str
    score: int
    work_type: str | None = None

class AIAnalysisResponse(AIAnalysisBase):
    id: UUID
    call_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
