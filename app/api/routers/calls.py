from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.api.deps.database import get_db
from app.repositories.call import CallRepository
from app.repositories.processing_job import ProcessingJobRepository
from app.schemas.call import CallDetailedResponse, CallResponse
from app.schemas.processing_job import ProcessingJobResponse
from app.workers.tasks import download_call_task

router = APIRouter()

@router.post("/scan", response_model=list[str])
async def trigger_drive_scan(db: AsyncSession = Depends(get_db)):
    from app.services.google_drive import GoogleDriveService
    from app.repositories.call import CallRepository
    from app.models.call import Call
    from sqlalchemy import select
    
    drive_service = GoogleDriveService(db)
    new_ids = await drive_service.scan_and_register_new_calls()
    
    # Only trigger the first call if no calls are currently actively processing
    call_repo = CallRepository(db)
    active_calls = await db.execute(
        select(Call).filter(Call.status.in_(["PROCESSING", "PENDING_ANALYSIS", "PENDING_SHEETS"]))
    )
    if not active_calls.scalars().all():
        next_call = await call_repo.get_next_pending()
        if next_call:
            download_call_task.delay(str(next_call.id))
            
    return new_ids

@router.get("/calls", response_model=list[CallResponse])
async def list_calls(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    repo = CallRepository(db)
    return await repo.get_all(skip=skip, limit=limit)

@router.get("/calls/{id}", response_model=CallDetailedResponse)
async def get_call(id: UUID, db: AsyncSession = Depends(get_db)):
    repo = CallRepository(db)
    call = await repo.get_with_details(str(id))
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call record not found"
        )
    return call

@router.post("/reprocess/{id}", response_model=CallResponse)
async def reprocess_call(id: UUID, db: AsyncSession = Depends(get_db)):
    repo = CallRepository(db)
    job_repo = ProcessingJobRepository(db)

    call = await repo.get(id)
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call record not found"
        )

    call.status = "PENDING_DOWNLOAD"

    job = await job_repo.get_by_call_and_task(call.id, "DOWNLOAD")
    if job:
        job.status = "PENDING"
        job.retries = 0
        job.error_message = None
    else:
        await job_repo.create({
            "call_id": call.id,
            "task_type": "DOWNLOAD",
            "status": "PENDING",
            "max_retries": 3
        })

    await db.commit()

    download_call_task.delay(str(call.id))

    return call

@router.post("/reprocess-all", response_model=list[str])
async def reprocess_all_calls(db: AsyncSession = Depends(get_db)):
    repo = CallRepository(db)
    job_repo = ProcessingJobRepository(db)
    
    # Get all calls using base repository get_all
    calls = await repo.get_all(skip=0, limit=1000)
    requeued_ids = []
    
    for call in calls:
        call.status = "PENDING_DOWNLOAD"
        
        job = await job_repo.get_by_call_and_task(call.id, "DOWNLOAD")
        if job:
            job.status = "PENDING"
            job.retries = 0
            job.error_message = None
        else:
            await job_repo.create({
                "call_id": call.id,
                "task_type": "DOWNLOAD",
                "status": "PENDING",
                "max_retries": 3
            })
            
        requeued_ids.append(str(call.id))
        
    await db.commit()
    
    # Trigger ONLY the first one to start the sequential pipeline!
    if requeued_ids:
        download_call_task.delay(requeued_ids[0])
        
    return requeued_ids

@router.get("/failed-jobs", response_model=list[ProcessingJobResponse])
async def list_failed_jobs(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    job_repo = ProcessingJobRepository(db)
    return await job_repo.get_failed_jobs(skip=skip, limit=limit)
