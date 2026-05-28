from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.call import Call
from app.repositories.base import BaseRepository

class CallRepository(BaseRepository[Call]):
    def __init__(self, session: AsyncSession):
        super().__init__(Call, session)

    async def get_by_gdrive_file_id(self, gdrive_file_id: str) -> Call | None:
        result = await self.session.execute(select(Call).filter_by(gdrive_file_id=gdrive_file_id))
        return result.scalar_one_or_none()

    async def get_with_details(self, id: str) -> Call | None:
        result = await self.session.execute(
            select(Call)
            .filter_by(id=id)
            .options(
                selectinload(Call.manager),
                selectinload(Call.transcript),
                selectinload(Call.ai_analysis),
                selectinload(Call.processing_jobs)
            )
        )
        return result.scalar_one_or_none()

    async def get_next_pending(self) -> Call | None:
        result = await self.session.execute(
            select(Call)
            .filter_by(status="PENDING_DOWNLOAD")
            .order_by(Call.created_at.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()
