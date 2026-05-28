from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class ManagerBase(BaseModel):
    name: str

class ManagerCreate(ManagerBase):
    pass

class ManagerResponse(ManagerBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
