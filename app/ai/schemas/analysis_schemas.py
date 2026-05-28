from pydantic import BaseModel, Field

class CallAnalysisSchema(BaseModel):
    manager_name: str = Field(description="Name of the manager extracted from the call")
    script_started_correctly: int = Field(description="1 if the manager introduced themselves and opened the script correctly, 0 otherwise")
    asked_vin: int = Field(description="1 if the manager asked for the VIN number of the car, 0 otherwise")
    asked_mileage: int = Field(description="1 if the manager asked for the car mileage, 0 otherwise")
    offered_diagnostics: int = Field(description="1 if the manager offered vehicle diagnostics, 0 otherwise")
    asked_repair_history: int = Field(description="1 if the manager asked for repair history, 0 otherwise")
    service_booking: int = Field(description="1 if the manager booked the service call, 0 otherwise")
    correct_termination: int = Field(description="1 if the manager closed the call properly, 0 otherwise")
    rude: int = Field(description="1 if the manager was rude or impolite, 0 otherwise")
    conflict: int = Field(description="1 if there was a verbal conflict initiated or maintained by the manager, 0 otherwise")
    answered_topic: int = Field(description="1 if the manager answered all user questions adequately, 0 otherwise")
    toxic: int = Field(description="1 if the manager responded with toxicity or sarcasm, 0 otherwise")
    violations: int = Field(description="1 if any script violations occurred, 0 otherwise")
    needs_attention: bool = Field(description="true if manager was rude, conflicted, interrupted, toxic, ignored questions, or lacked basic skills")
    issue_type: str | None = Field(None, description="Detailed category of issue if needs_attention is true, e.g. manager_conflict, impoliteness")
    manager_comment: str = Field(description="Detailed comment highlighting compliance, scored with ALERT prefix if needs_attention is true")
    score: int = Field(description="Evaluated manager score based on checklist rules")
    work_type: str = Field(description="Type of vehicle work requested by the client, e.g., 'ТО', 'Діагностика', 'Ремонт двигуна', 'Ходова', or 'Інше' if not clearly mentioned")

    # Custom metrics
    request_type: str = Field(description="Type of request/call: 'Вхідний дзвінок', 'Запис', 'Авто в роботі', 'Консультація', 'Скарга', or 'Інше'")
    branch: str | None = Field(None, description="Auto service branch/location if mentioned in the call, otherwise null")
    asked_car_body: int = Field(description="1 if the manager found out/asked for the car body type, 0 otherwise")
    asked_car_year: int = Field(description="1 if the manager found out/asked for the car year, 0 otherwise")
    service_booking_date: str | None = Field(None, description="Date/time of the booking if scheduled, otherwise null")
    is_top_100_compliant: str = Field(description="'Да' if the manager fully followed all instructions for the top 100 works, 'Ні' otherwise")
    top_100_non_compliant_recommendations: str | None = Field(None, description="Details of instructions manager failed to follow from the top 100 list")
    violations_result: str | None = Field(None, description="Brief explanation of results/violations, e.g. 'Не уточнив правильних установок...'")
    spare_parts: str | None = Field(None, description="Spare parts discussed, description or null")

class AIAnalysisResponse(BaseModel):
    analysis: CallAnalysisSchema
