import asyncio
from typing import Any
import structlog
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from celery.exceptions import Retry
from app.workers.celery_app import celery_app
from app.core.config.settings import settings
from app.services.google_drive import GoogleDriveService
from app.services.call_processor import CallProcessorService
from app.core.logging.structlog_config import set_correlation_id

logger = structlog.get_logger(__name__)

def _make_session():
    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=1,
        max_overflow=0
    )
    factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    return engine, factory

def run_async(coro) -> Any:
    return asyncio.run(coro)

async def _trigger_next_if_any():
    engine, factory = _make_session()
    try:
        async with factory() as session:
            from app.repositories.call import CallRepository
            call_repo = CallRepository(session)
            next_call = await call_repo.get_next_pending()
            if next_call:
                logger.info("Triggering next call in sequential queue", next_call_id=str(next_call.id))
                download_call_task.delay(str(next_call.id))
    except Exception as e:
        logger.error("Failed to trigger next call in sequential queue", error=str(e))
    finally:
        await engine.dispose()

@celery_app.task(name="app.workers.tasks.scan_drive_task")
def scan_drive_task() -> list[str]:
    async def run():
        engine, factory = _make_session()
        try:
            async with factory() as session:
                drive_service = GoogleDriveService(session)
                new_ids = await drive_service.scan_and_register_new_calls()
                
                # Sequential trigger check:
                # If there are no currently active/processing calls, start the first pending call!
                from app.repositories.call import CallRepository
                from app.models.call import Call
                from sqlalchemy import select
                
                call_repo = CallRepository(session)
                active_calls = await session.execute(
                    select(Call).filter(Call.status.in_(["PROCESSING", "PENDING_ANALYSIS", "PENDING_SHEETS"]))
                )
                if not active_calls.scalars().all():
                    next_call = await call_repo.get_next_pending()
                    if next_call:
                        logger.info("Sequential pipeline idle. Starting next call.", next_call_id=str(next_call.id))
                        download_call_task.delay(str(next_call.id))
                
                return new_ids
        finally:
            await engine.dispose()
    return run_async(run())

@celery_app.task(name="app.workers.tasks.download_call_task", bind=True, max_retries=3)
def download_call_task(self, call_id: str) -> str:
    set_correlation_id(call_id)
    async def run():
        engine, factory = _make_session()
        try:
            async with factory() as session:
                drive_service = GoogleDriveService(session)
                path = await drive_service.download_call_audio(call_id)
                transcribe_call_task.delay(call_id)
                return path
        finally:
            await engine.dispose()
    try:
        return run_async(run())
    except Exception as e:
        logger.error("Download task failed, retrying...", call_id=call_id, error=str(e))
        try:
            raise self.retry(exc=e, countdown=10)
        except Retry as r:
            raise r
        except Exception as final_exc:
            run_async(_trigger_next_if_any())
            raise final_exc

@celery_app.task(name="app.workers.tasks.transcribe_call_task", bind=True, max_retries=3)
def transcribe_call_task(self, call_id: str) -> str:
    set_correlation_id(call_id)
    async def run():
        engine, factory = _make_session()
        try:
            async with factory() as session:
                processor = CallProcessorService(session)
                text = await processor.transcribe_call(call_id)
                analyze_call_task.delay(call_id)
                return text
        finally:
            await engine.dispose()
    try:
        return run_async(run())
    except Exception as e:
        logger.error("Transcription task failed, retrying...", call_id=call_id, error=str(e))
        try:
            raise self.retry(exc=e, countdown=15)
        except Retry as r:
            raise r
        except Exception as final_exc:
            run_async(_trigger_next_if_any())
            raise final_exc

@celery_app.task(name="app.workers.tasks.analyze_call_task", bind=True, max_retries=3)
def analyze_call_task(self, call_id: str) -> None:
    set_correlation_id(call_id)
    async def run():
        engine, factory = _make_session()
        try:
            async with factory() as session:
                processor = CallProcessorService(session)
                await processor.analyze_call(call_id)
                sync_sheets_task.delay(call_id)
        finally:
            await engine.dispose()
    try:
        return run_async(run())
    except Exception as e:
        logger.error("Analysis task failed, retrying...", call_id=call_id, error=str(e))
        try:
            raise self.retry(exc=e, countdown=10)
        except Retry as r:
            raise r
        except Exception as final_exc:
            run_async(_trigger_next_if_any())
            raise final_exc

@celery_app.task(name="app.workers.tasks.sync_sheets_task", bind=True, max_retries=3)
def sync_sheets_task(self, call_id: str) -> None:
    set_correlation_id(call_id)
    print(f"CELERY TASK: Entering sync_sheets_task for call_id={call_id}", flush=True)
    async def run():
        engine, factory = _make_session()
        try:
            async with factory() as session:
                processor = CallProcessorService(session)
                print(f"CELERY TASK: Calling synchronize_call_data in CallProcessorService for call_id={call_id}...", flush=True)
                await processor.synchronize_call_data(call_id)
                
                # Successful sync! Trigger next call in sequential queue
                from app.repositories.call import CallRepository
                call_repo = CallRepository(session)
                next_call = await call_repo.get_next_pending()
                if next_call:
                    logger.info("Sync completed. Triggering next call in sequential queue", next_call_id=str(next_call.id))
                    print(f"CELERY TASK: Sync completed successfully. Triggering next call_id={str(next_call.id)}...", flush=True)
                    download_call_task.delay(str(next_call.id))
                else:
                    print("CELERY TASK: Sync completed successfully. No more pending calls in queue.", flush=True)
        finally:
            await engine.dispose()
    try:
        return run_async(run())
    except Exception as e:
        logger.error("Sync sheets task failed, retrying...", call_id=call_id, error=str(e))
        print(f"CELERY TASK ERROR: sync_sheets_task failed for call_id={call_id}. Error: {str(e)}", flush=True)
        try:
            raise self.retry(exc=e, countdown=20)
        except Retry as r:
            raise r
        except Exception as final_exc:
            print(f"CELERY TASK FATAL: sync_sheets_task exhausted all retries for call_id={call_id}. Triggering next if any...", flush=True)
            run_async(_trigger_next_if_any())
            raise final_exc
