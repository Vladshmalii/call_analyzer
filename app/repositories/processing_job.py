from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.processing_job import ProcessingJob
from app.repositories.base import BaseRepository

class ProcessingJobRepository(BaseRepository[ProcessingJob]):
    def __init__(self, session: AsyncSession):
        super().__init__(ProcessingJob, session)

    async def get_by_call_and_task(self, call_id: str, task_type: str) -> ProcessingJob | None:
        result = await self.session.execute(
            select(ProcessingJob).filter_by(call_id=call_id, task_type=task_type)
        )
        return result.scalar_one_or_none()

    async def get_failed_jobs(self, skip: int = 0, limit: int = 100) -> list[ProcessingJob]:
        result = await self.session.execute(
            select(ProcessingJob).filter_by(status="FAILED").offset(skip).limit(limit)
        )
        return list(result.scalars().all())
