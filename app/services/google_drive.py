import os
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
from app.integrations.google_drive.drive_client import GoogleDriveClient
from app.repositories.call import CallRepository
from app.repositories.processing_job import ProcessingJobRepository
from app.repositories.processing_log import ProcessingLogRepository
from app.core.config.settings import settings

logger = structlog.get_logger(__name__)

class GoogleDriveService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.drive_client = GoogleDriveClient()
        self.call_repo = CallRepository(session)
        self.job_repo = ProcessingJobRepository(session)
        self.log_repo = ProcessingLogRepository(session)

    async def scan_and_register_new_calls(self) -> list[str]:
        drive_files = await self.drive_client.list_files()
        new_call_ids = []

        for file_data in drive_files:
            file_id = file_data["id"]
            file_name = file_data["name"]

            existing = await self.call_repo.get_by_gdrive_file_id(file_id)
            if existing:
                continue

            shortcut_created = await self.drive_client.create_shortcut(file_id, file_name)
            if not shortcut_created:
                logger.warning("Could not create shortcut in working folder, proceeding anyway", file_name=file_name)

            call_in = {
                "gdrive_file_id": file_id,
                "file_name": file_name,
                "status": "PENDING_DOWNLOAD"
            }
            call = await self.call_repo.create(call_in)

            job_in = {
                "call_id": call.id,
                "task_type": "DOWNLOAD",
                "status": "PENDING",
                "max_retries": 3
            }
            await self.job_repo.create(job_in)

            log_in = {
                "call_id": call.id,
                "level": "INFO",
                "message": f"Registered file: {file_name}",
                "context": file_data
            }
            await self.log_repo.create(log_in)
            new_call_ids.append(str(call.id))

        await self.session.commit()
        logger.info("Drive scan completed", new_files=len(new_call_ids))
        return new_call_ids

    async def download_call_audio(self, call_id: str) -> str:
        call = await self.call_repo.get(call_id)
        if not call:
            raise ValueError(f"Call with ID {call_id} not found")

        job = await self.job_repo.get_by_call_and_task(call.id, "DOWNLOAD")
        if job:
            job.status = "PROCESSING"
            await self.session.flush()

        destination_path = os.path.join(
            settings.LOCAL_STORAGE_DIR,
            f"{call.id}_{call.file_name}"
        )

        success = await self.drive_client.download_file(call.gdrive_file_id, destination_path)
        if not success:
            if job:
                job.status = "FAILED"
                job.error_message = "Google Drive download failed"
            call.status = "FAILED"
            await self.log_repo.create({
                "call_id": call.id,
                "level": "ERROR",
                "message": "Failed to download audio file from Google Drive"
            })
            await self.session.commit()
            raise RuntimeError(f"Google Drive download failed for file {call.gdrive_file_id}")

        call.file_path = destination_path
        call.status = "PENDING_TRANSCRIPTION"
        if job:
            job.status = "COMPLETED"

        await self.log_repo.create({
            "call_id": call.id,
            "level": "INFO",
            "message": f"Successfully downloaded file to {destination_path}"
        })
        await self.session.commit()
        return destination_path
