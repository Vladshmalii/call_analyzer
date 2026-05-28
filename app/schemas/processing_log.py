from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class ProcessingLogBase(BaseModel):
    level: str
    message: str
    context: dict | list | None

class ProcessingLogResponse(ProcessingLogBase):
    id: UUID
    call_id: UUID | None
    created_at: datetime

    class Config:
        from_attributes = True
