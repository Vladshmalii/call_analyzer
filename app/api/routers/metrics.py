from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.api.deps.database import get_db
from app.models.call import Call
from app.models.ai_analysis import AIAnalysis

router = APIRouter()

@router.get("/metrics")
async def get_system_metrics(db: AsyncSession = Depends(get_db)):
    total_calls_query = await db.execute(select(func.count(Call.id)))
    total_calls = total_calls_query.scalar() or 0

    completed_calls_query = await db.execute(select(func.count(Call.id)).filter_by(status="COMPLETED"))
    completed_calls = completed_calls_query.scalar() or 0

    failed_calls_query = await db.execute(select(func.count(Call.id)).filter_by(status="FAILED"))
    failed_calls = failed_calls_query.scalar() or 0

    avg_score_query = await db.execute(select(func.avg(AIAnalysis.score)))
    avg_score = float(avg_score_query.scalar() or 0.0)

    attention_calls_query = await db.execute(select(func.count(AIAnalysis.id)).filter_by(needs_attention=True))
    attention_calls = attention_calls_query.scalar() or 0

    violations_calls_query = await db.execute(select(func.count(AIAnalysis.id)).filter_by(violations=True))
    violations_calls = violations_calls_query.scalar() or 0

    return {
        "total_calls": total_calls,
        "completed_calls": completed_calls,
        "failed_calls": failed_calls,
        "average_score": round(avg_score, 2),
        "needs_attention_count": attention_calls,
        "violations_count": violations_calls
    }
