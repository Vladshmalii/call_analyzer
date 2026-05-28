from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from app.schemas.manager import ManagerResponse
from app.schemas.ai_analysis import AIAnalysisResponse
from app.schemas.processing_job import ProcessingJobResponse

class CallBase(BaseModel):
    gdrive_file_id: str | None
    file_name: str
    file_path: str | None
    duration: int | None
    status: str

class CallCreate(CallBase):
    pass

class CallResponse(CallBase):
    id: UUID
    manager_id: UUID | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CallDetailedResponse(CallResponse):
    manager: ManagerResponse | None = None
    ai_analysis: AIAnalysisResponse | None = None
    processing_jobs: list[ProcessingJobResponse] = []

    class Config:
        from_attributes = True
