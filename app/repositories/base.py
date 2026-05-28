from typing import Generic, TypeVar, Type, Sequence, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: UUID) -> ModelType | None:
        result = await self.session.execute(select(self.model).filter_by(id=id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        result = await self.session.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, obj_in: dict[str, Any]) -> ModelType:
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        await self.session.flush()
        return db_obj

    async def update(self, id: UUID, obj_in: dict[str, Any]) -> ModelType | None:
        await self.session.execute(
            update(self.model).filter_by(id=id).values(**obj_in)
        )
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(self.model).filter_by(id=id)
        )
        return result.rowcount > 0
