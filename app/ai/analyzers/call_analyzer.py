from typing import Any
import structlog
from app.ai.providers.groq_provider import GroqProvider
from app.ai.schemas.analysis_schemas import CallAnalysisSchema

logger = structlog.get_logger(__name__)

class CallAnalyzer:
    def __init__(self):
        self.provider = GroqProvider()

    async def analyze(self, transcript_text: str) -> CallAnalysisSchema:
        raw_result = await self.provider.analyze_transcript(transcript_text)
        return self._post_process(raw_result)

    def _post_process(self, raw_data: dict[str, Any]) -> CallAnalysisSchema:
        if not isinstance(raw_data, dict):
            raw_data = {}
            
        manager_name = raw_data.get("manager_name") or "Unknown"
        
        def safe_int(val, default=0) -> int:
            if val is None:
                return default
            try:
                return int(val)
            except (ValueError, TypeError):
                return default

        script_started_correctly = safe_int(raw_data.get("script_started_correctly"), 0)
        asked_vin = safe_int(raw_data.get("asked_vin"), 0)
        asked_mileage = safe_int(raw_data.get("asked_mileage"), 0)
        offered_diagnostics = safe_int(raw_data.get("offered_diagnostics"), 0)
        asked_repair_history = safe_int(raw_data.get("asked_repair_history"), 0)
        service_booking = safe_int(raw_data.get("service_booking"), 0)
        correct_termination = safe_int(raw_data.get("correct_termination"), 0)
        rude = safe_int(raw_data.get("rude"), 0)
        conflict = safe_int(raw_data.get("conflict"), 0)
        answered_topic = safe_int(raw_data.get("answered_topic"), 1)
        toxic = safe_int(raw_data.get("toxic"), 0)
        violations = safe_int(raw_data.get("violations"), 0)

        score = 0
        if script_started_correctly == 1:
            score += 1
        if asked_vin == 1:
            score += 1
        if asked_mileage == 1:
            score += 1
        if offered_diagnostics == 1:
            score += 1
        if service_booking == 1:
            score += 2
        if answered_topic == 0:
            score -= 2
        if rude == 1:
            score -= 3
        if conflict == 1:
            score -= 5

        needs_attention = False
        if rude == 1 or conflict == 1 or toxic == 1 or answered_topic == 0:
            needs_attention = True
        if raw_data.get("needs_attention") is True:
            needs_attention = True

        issue_type = raw_data.get("issue_type")
        if needs_attention and not issue_type:
            if conflict == 1:
                issue_type = "manager_conflict"
            elif rude == 1 or toxic == 1:
                issue_type = "impoliteness"
            else:
                issue_type = "script_deviation"

        manager_comment = raw_data.get("manager_comment", "")
        if needs_attention:
            if not manager_comment.startswith("ALERT:"):
                manager_comment = f"ALERT: {manager_comment}"

        work_type = raw_data.get("work_type") or "Інше"

        request_type = raw_data.get("request_type") or "Вхідний дзвінок"
        branch = raw_data.get("branch")
        asked_car_body = safe_int(raw_data.get("asked_car_body"), 0)
        asked_car_year = safe_int(raw_data.get("asked_car_year"), 0)
        service_booking_date = raw_data.get("service_booking_date")
        is_top_100_compliant = raw_data.get("is_top_100_compliant") or "Ні"
        top_100_non_compliant_recommendations = raw_data.get("top_100_non_compliant_recommendations")
        violations_result = raw_data.get("violations_result")
        spare_parts = raw_data.get("spare_parts")

        validated = CallAnalysisSchema(
            manager_name=manager_name,
            script_started_correctly=script_started_correctly,
            asked_vin=asked_vin,
            asked_mileage=asked_mileage,
            offered_diagnostics=offered_diagnostics,
            asked_repair_history=asked_repair_history,
            service_booking=service_booking,
            correct_termination=correct_termination,
            rude=rude,
            conflict=conflict,
            answered_topic=answered_topic,
            toxic=toxic,
            violations=violations,
            needs_attention=needs_attention,
            issue_type=issue_type,
            manager_comment=manager_comment,
            score=score,
            work_type=work_type,
            request_type=request_type,
            branch=branch,
            asked_car_body=asked_car_body,
            asked_car_year=asked_car_year,
            service_booking_date=service_booking_date,
            is_top_100_compliant=is_top_100_compliant,
            top_100_non_compliant_recommendations=top_100_non_compliant_recommendations,
            violations_result=violations_result,
            spare_parts=spare_parts
        )
        return validated
