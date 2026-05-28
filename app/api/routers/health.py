from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as ar
from app.api.deps.database import get_db
from app.core.config.settings import settings

router = APIRouter()

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    redis_status = "healthy"
    try:
        r = ar.from_url(settings.REDIS_URL)
        await r.ping()
        await r.close()
    except Exception:
        redis_status = "unhealthy"

    status = "healthy" if db_status == "healthy" and redis_status == "healthy" else "unhealthy"

    return {
        "status": status,
        "database": db_status,
        "redis": redis_status,
        "project": settings.PROJECT_NAME
    }
