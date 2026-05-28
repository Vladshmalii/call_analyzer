from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class ProcessingJobBase(BaseModel):
    task_type: str
    status: str
    retries: int
    max_retries: int
    error_message: str | None

class ProcessingJobResponse(ProcessingJobBase):
    id: UUID
    call_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProcessingJobReprocess(BaseModel):
    call_id: UUID
