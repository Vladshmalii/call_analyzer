import uuid
import pytest
import pytest_asyncio
from sqlalchemy import select, event
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.database.session import Base
# Import all models so their tables register on Base.metadata.
from app.models.call import Call
from app.models.transcript import Transcript
from app.models.processing_job import ProcessingJob
from app.models import manager, ai_analysis, processing_log  # noqa: F401
from app.repositories.call import CallRepository


@pytest_asyncio.fixture
async def session():
    """Isolated in-memory SQLite session with FK cascade enforcement."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # SQLite ignores foreign keys unless the pragma is set per connection.
    @event.listens_for(engine.sync_engine, "connect")
    def _fk_pragma(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s

    await engine.dispose()


async def _make_call(session, **overrides) -> Call:
    data = {"id": uuid.uuid4(), "file_name": "test-call.mp3", "status": "COMPLETED"}
    data.update(overrides)
    call = Call(**data)
    session.add(call)
    await session.flush()
    return call


@pytest.mark.asyncio
async def test_delete_call_success(session):
    repo = CallRepository(session)
    call = await _make_call(session)
    await session.commit()

    deleted = await repo.delete(call.id)
    await session.commit()

    assert deleted is True
    result = await session.execute(select(Call).filter_by(id=call.id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_delete_call_missing_returns_false(session):
    repo = CallRepository(session)
    deleted = await repo.delete(uuid.uuid4())
    assert deleted is False


@pytest.mark.asyncio
async def test_delete_call_cascades_children(session):
    repo = CallRepository(session)
    call = await _make_call(session)
    session.add(Transcript(id=uuid.uuid4(), call_id=call.id, raw_text="hi"))
    session.add(
        ProcessingJob(id=uuid.uuid4(), call_id=call.id, task_type="DOWNLOAD", status="PENDING")
    )
    await session.commit()

    deleted = await repo.delete(call.id)
    await session.commit()

    assert deleted is True
    tr = await session.execute(select(Transcript).filter_by(call_id=call.id))
    assert tr.scalar_one_or_none() is None
    jobs = await session.execute(select(ProcessingJob).filter_by(call_id=call.id))
    assert jobs.scalars().all() == []
