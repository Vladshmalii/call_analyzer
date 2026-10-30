import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.api.deps.database import get_db
from app.core.database.session import Base
from app.models.call import Call
from app.models import transcript, processing_job, manager, ai_analysis, processing_log  # noqa: F401


@pytest_asyncio.fixture
async def client_and_factory():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _fk_pragma(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_get_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, factory

    app.dependency_overrides.pop(get_db, None)
    await engine.dispose()


@pytest.mark.asyncio
async def test_delete_call_endpoint_success(client_and_factory):
    client, factory = client_and_factory
    call_id = uuid.uuid4()
    async with factory() as s:
        s.add(Call(id=call_id, file_name="c.mp3", status="COMPLETED"))
        await s.commit()

    resp = await client.delete(f"/api/v1/calls/{call_id}")
    assert resp.status_code == 204

    # Second delete of the same id now 404s.
    resp2 = await client.delete(f"/api/v1/calls/{call_id}")
    assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_delete_call_endpoint_not_found(client_and_factory):
    client, _ = client_and_factory
    resp = await client.delete(f"/api/v1/calls/{uuid.uuid4()}")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Call record not found"


@pytest.mark.asyncio
async def test_delete_call_endpoint_invalid_uuid(client_and_factory):
    client, _ = client_and_factory
    resp = await client.delete("/api/v1/calls/not-a-uuid")
    assert resp.status_code == 422
