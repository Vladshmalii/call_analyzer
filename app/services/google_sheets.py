from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
from app.integrations.google_sheets.sheets_client import GoogleSheetsClient
from app.repositories.call import CallRepository
from app.repositories.ai_analysis import AIAnalysisRepository
from app.repositories.processing_job import ProcessingJobRepository
from app.repositories.processing_log import ProcessingLogRepository

logger = structlog.get_logger(__name__)

class GoogleSheetsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.sheets_client = GoogleSheetsClient()
        self.call_repo = CallRepository(session)
        self.analysis_repo = AIAnalysisRepository(session)
        self.job_repo = ProcessingJobRepository(session)
        self.log_repo = ProcessingLogRepository(session)

    async def update_sheets_for_call(self, call_id: str) -> bool:
        call = await self.call_repo.get(call_id)
        if not call:
            return False

        analysis = await self.analysis_repo.get_by_call_id(call.id)
        if not analysis:
            return False

        job = await self.job_repo.get_by_call_and_task(call.id, "GOOGLE_SHEETS")
        if job:
            job.status = "PROCESSING"
            await self.session.flush()

        # Filename format: YYYY-MM-DD_HH-MM_phone_direction.mp3
        # e.g. 2025-08-15_11-37_0634526845_incoming.mp3
        parts = call.file_name.split("_")
        date_str = call.created_at.strftime("%d.%m.%Y")
        phone_placeholder = call.file_name
        
        if len(parts) >= 3:
            try:
                dt = datetime.strptime(parts[0], "%Y-%m-%d")
                date_str = dt.strftime("%d.%m.%Y")
            except Exception:
                pass
            phone_placeholder = parts[2]


        recommendations = []
        if not analysis.script_started_correctly:
            recommendations.append("Привітатись та представитись за скриптом")
        if not analysis.asked_vin:
            recommendations.append("Запитати VIN-код автомобіля")
        if not analysis.asked_mileage:
            recommendations.append("Запитати поточний пробіг")
        if not analysis.offered_diagnostics:
            recommendations.append("Запропонувати комплексну діагностику")
        if not analysis.service_booking:
            recommendations.append("Спробувати записати клієнта на візит")

        mgr_comment = analysis.manager_comment or ""
        if mgr_comment.upper().startswith("ALERT:"):
            mgr_comment = mgr_comment[6:].strip()
        elif mgr_comment.upper().startswith("ALERT"):
            mgr_comment = mgr_comment[5:].strip()

        rec_text = "; ".join(recommendations) if recommendations else "Дотримано всіх вимог"
        full_comment = f"{mgr_comment} | Рекомендації: {rec_text}"

        def map_bool(val: bool) -> int:
            return 1 if val else 2

        row_data = [
            date_str,                                                               # 1. Дата
            analysis.request_type if analysis.request_type else "Вхідний дзвінок", # 2. Тип звернення
            phone_placeholder,                                                     # 3. Номер телефону
            analysis.branch if analysis.branch else "",                            # 4. Філія
            analysis.manager_name,                                                 # 5. Менеджер
            map_bool(analysis.script_started_correctly),                           # 6. Початок розмови, представлення
            map_bool(analysis.asked_car_body),                                     # 7. Чи дізнвся менеджер кузов атвомобіля
            map_bool(analysis.asked_car_year),                                     # 8. Чи дізнався менеджер рік автомобіля
            map_bool(analysis.asked_mileage),                                      # 9. Чи дізнався менеджр пробіг
            map_bool(analysis.offered_diagnostics),                                # 10. Пропозиція про комплексну діагностику
            map_bool(analysis.asked_repair_history),                               # 11. Дізнався які роботи робилися раніше
            analysis.service_booking_date if analysis.service_booking_date else "", # 12. Запис на сервіс, Дата
            map_bool(analysis.correct_termination),                                 # 13. Завершення розмови прощання
            analysis.work_type if analysis.work_type else "Інше",                  # 14. Яка робота з топ 100
            analysis.is_top_100_compliant if analysis.is_top_100_compliant else "Ні", # 15. Чи дотримувався всіх інструкцій з топ 100 робіт Да/Ні
            analysis.top_100_non_compliant_recommendations if analysis.top_100_non_compliant_recommendations else "", # 16. Яких рекоменадцій менеджер не дотримувався з топ 100 робіт
            analysis.violations_result if analysis.violations_result else "",       # 17. Результат
            analysis.score,                                                        # 18. Оцінка
            analysis.spare_parts if analysis.spare_parts else "",                  # 19. Запчастини
            full_comment                                                           # 20. Коментар
        ]

        logger.info("Prepared Google Sheets row data", call_id=call_id, spreadsheet_id=self.sheets_client.spreadsheet_id, row_data=row_data)
        print(f"GOOGLE_SHEETS_SERVICE: Preparing to write call_id={call_id} to sheet. Spreadsheet ID={self.sheets_client.spreadsheet_id}", flush=True)
        print(f"GOOGLE_SHEETS_SERVICE: Row data to append: {row_data}", flush=True)

        success = await self.sheets_client.append_row(row_data, needs_attention=analysis.needs_attention)
        if not success:
            logger.error("Failed to append row to Google Sheets", call_id=call_id)
            print(f"GOOGLE_SHEETS_SERVICE ERROR: Failed to append row for call_id={call_id} to spreadsheet", flush=True)
            if job:
                job.status = "FAILED"
                job.error_message = "Google Sheets API append failed"
            await self.log_repo.create({
                "call_id": call.id,
                "level": "ERROR",
                "message": "Failed to update Google Sheets"
            })
            await self.session.commit()
            return False

        logger.info("Successfully appended row to Google Sheets", call_id=call_id)
        print(f"GOOGLE_SHEETS_SERVICE SUCCESS: Successfully appended row for call_id={call_id}", flush=True)


        call.status = "COMPLETED"
        if job:
            job.status = "COMPLETED"

        await self.log_repo.create({
            "call_id": call.id,
            "level": "INFO",
            "message": "Successfully synchronized analysis data with Google Sheets"
        })
        await self.session.commit()
        return True
