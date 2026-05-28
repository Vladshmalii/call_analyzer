from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.processing_log import ProcessingLog
from app.repositories.base import BaseRepository

class ProcessingLogRepository(BaseRepository[ProcessingLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(ProcessingLog, session)

    async def get_by_call_id(self, call_id: str) -> list[ProcessingLog]:
        result = await self.session.execute(
            select(ProcessingLog).filter_by(call_id=call_id).order_by(ProcessingLog.created_at.asc())
        )
        return list(result.scalars().all())
