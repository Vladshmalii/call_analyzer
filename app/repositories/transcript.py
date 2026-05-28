from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.transcript import Transcript
from app.repositories.base import BaseRepository

class TranscriptRepository(BaseRepository[Transcript]):
    def __init__(self, session: AsyncSession):
        super().__init__(Transcript, session)

    async def get_by_call_id(self, call_id: str) -> Transcript | None:
        result = await self.session.execute(select(Transcript).filter_by(call_id=call_id))
        return result.scalar_one_or_none()
