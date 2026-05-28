from sqlalchemy.ext.asyncio import AsyncSession
import structlog
from app.repositories.call import CallRepository
from app.repositories.manager import ManagerRepository
from app.repositories.transcript import TranscriptRepository
from app.repositories.ai_analysis import AIAnalysisRepository
from app.repositories.processing_job import ProcessingJobRepository
from app.repositories.processing_log import ProcessingLogRepository
from app.services.transcription import FasterWhisperProvider
from app.ai.analyzers.call_analyzer import CallAnalyzer
from app.services.google_sheets import GoogleSheetsService

logger = structlog.get_logger(__name__)

class CallProcessorService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.call_repo = CallRepository(session)
        self.manager_repo = ManagerRepository(session)
        self.transcript_repo = TranscriptRepository(session)
        self.analysis_repo = AIAnalysisRepository(session)
        self.job_repo = ProcessingJobRepository(session)
        self.log_repo = ProcessingLogRepository(session)
        self.transcriber = FasterWhisperProvider()
        self.analyzer = CallAnalyzer()
        self.sheets_service = GoogleSheetsService(session)

    async def transcribe_call(self, call_id: str) -> str:
        call = await self.call_repo.get(call_id)
        if not call:
            raise ValueError(f"Call with ID {call_id} not found")

        job = await self.job_repo.get_by_call_and_task(call.id, "TRANSCRIPTION")
        if not job:
            job = await self.job_repo.create({
                "call_id": call.id,
                "task_type": "TRANSCRIPTION",
                "status": "PENDING"
            })

        job.status = "PROCESSING"
        call.status = "PROCESSING"
        await self.session.flush()

        try:
            result = await self.transcriber.transcribe(call.file_path)
            call.duration = int(result["duration"])

            existing_transcript = await self.transcript_repo.get_by_call_id(call.id)
            if existing_transcript:
                existing_transcript.raw_text = result["raw_text"]
                existing_transcript.segments = result["segments"]
            else:
                await self.transcript_repo.create({
                    "call_id": call.id,
                    "raw_text": result["raw_text"],
                    "segments": result["segments"]
                })

            call.status = "PENDING_ANALYSIS"
            job.status = "COMPLETED"

            await self.log_repo.create({
                "call_id": call.id,
                "level": "INFO",
                "message": "Call audio successfully transcribed"
            })
            await self.session.commit()
            return result["raw_text"]
        except Exception as e:
            job.status = "FAILED"
            job.error_message = str(e)
            call.status = "FAILED"
            await self.log_repo.create({
                "call_id": call.id,
                "level": "ERROR",
                "message": f"Transcription failed: {str(e)}"
            })
            await self.session.commit()
            raise e

    async def analyze_call(self, call_id: str) -> None:
        call = await self.call_repo.get(call_id)
        if not call:
            raise ValueError(f"Call with ID {call_id} not found")

        transcript = await self.transcript_repo.get_by_call_id(call.id)
        if not transcript:
            raise ValueError(f"Transcript for call {call_id} not found")

        job = await self.job_repo.get_by_call_and_task(call.id, "AI_ANALYSIS")
        if not job:
            job = await self.job_repo.create({
                "call_id": call.id,
                "task_type": "AI_ANALYSIS",
                "status": "PENDING"
            })

        job.status = "PROCESSING"
        await self.session.flush()

        try:
            analysis_schema = await self.analyzer.analyze(transcript.raw_text)

            manager_name = analysis_schema.manager_name
            manager = await self.manager_repo.get_by_name(manager_name)
            if not manager:
                manager = await self.manager_repo.create({"name": manager_name})

            call.manager_id = manager.id

            analysis_data = {
                "manager_name": manager_name,
                "script_started_correctly": analysis_schema.script_started_correctly == 1,
                "asked_vin": analysis_schema.asked_vin == 1,
                "asked_mileage": analysis_schema.asked_mileage == 1,
                "offered_diagnostics": analysis_schema.offered_diagnostics == 1,
                "asked_repair_history": analysis_schema.asked_repair_history == 1,
                "service_booking": analysis_schema.service_booking == 1,
                "correct_termination": analysis_schema.correct_termination == 1,
                "rude": analysis_schema.rude == 1,
                "conflict": analysis_schema.conflict == 1,
                "answered_topic": analysis_schema.answered_topic == 1,
                "toxic": analysis_schema.toxic == 1,
                "violations": analysis_schema.violations == 1,
                "needs_attention": analysis_schema.needs_attention,
                "issue_type": analysis_schema.issue_type,
                "manager_comment": analysis_schema.manager_comment,
                "score": analysis_schema.score,
                "work_type": analysis_schema.work_type,
                
                # New persisted metrics
                "request_type": analysis_schema.request_type,
                "branch": analysis_schema.branch,
                "asked_car_body": analysis_schema.asked_car_body == 1,
                "asked_car_year": analysis_schema.asked_car_year == 1,
                "service_booking_date": analysis_schema.service_booking_date,
                "is_top_100_compliant": analysis_schema.is_top_100_compliant,
                "top_100_non_compliant_recommendations": analysis_schema.top_100_non_compliant_recommendations,
                "violations_result": analysis_schema.violations_result,
                "spare_parts": analysis_schema.spare_parts
            }

            existing_analysis = await self.analysis_repo.get_by_call_id(call.id)
            if existing_analysis:
                for key, val in analysis_data.items():
                    setattr(existing_analysis, key, val)
            else:
                analysis_data["call_id"] = call.id
                await self.analysis_repo.create(analysis_data)

            call.status = "PENDING_SHEETS"
            job.status = "COMPLETED"

            await self.log_repo.create({
                "call_id": call.id,
                "level": "INFO",
                "message": "AI analysis of transcription completed"
            })
            await self.session.commit()
        except Exception as e:
            job.status = "FAILED"
            job.error_message = str(e)
            call.status = "FAILED"
            await self.log_repo.create({
                "call_id": call.id,
                "level": "ERROR",
                "message": f"AI Analysis failed: {str(e)}"
            })
            await self.session.commit()
            raise e

    async def synchronize_call_data(self, call_id: str) -> None:
        job = await self.job_repo.get_by_call_and_task(call_id, "GOOGLE_SHEETS")
        if not job:
            job = await self.job_repo.create({
                "call_id": call_id,
                "task_type": "GOOGLE_SHEETS",
                "status": "PENDING"
            })
            await self.session.flush()

        success = await self.sheets_service.update_sheets_for_call(call_id)
        if not success:
            raise RuntimeError("Synchronization to Google Sheets failed")
