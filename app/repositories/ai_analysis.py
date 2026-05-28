from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ai_analysis import AIAnalysis
from app.repositories.base import BaseRepository

class AIAnalysisRepository(BaseRepository[AIAnalysis]):
    def __init__(self, session: AsyncSession):
        super().__init__(AIAnalysis, session)

    async def get_by_call_id(self, call_id: str) -> AIAnalysis | None:
        result = await self.session.execute(select(AIAnalysis).filter_by(call_id=call_id))
        return result.scalar_one_or_none()
