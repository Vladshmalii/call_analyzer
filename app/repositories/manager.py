from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.manager import Manager
from app.repositories.base import BaseRepository

class ManagerRepository(BaseRepository[Manager]):
    def __init__(self, session: AsyncSession):
        super().__init__(Manager, session)

    async def get_by_name(self, name: str) -> Manager | None:
        result = await self.session.execute(select(Manager).filter_by(name=name))
        return result.scalar_one_or_none()
