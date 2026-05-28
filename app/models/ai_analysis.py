import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    call_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("calls.id", ondelete="CASCADE"), unique=True, nullable=False)
    manager_name: Mapped[str] = mapped_column(String(255), nullable=False)
    script_started_correctly: Mapped[bool] = mapped_column(Boolean, default=False)
    asked_vin: Mapped[bool] = mapped_column(Boolean, default=False)
    asked_mileage: Mapped[bool] = mapped_column(Boolean, default=False)
    offered_diagnostics: Mapped[bool] = mapped_column(Boolean, default=False)
    asked_repair_history: Mapped[bool] = mapped_column(Boolean, default=False)
    service_booking: Mapped[bool] = mapped_column(Boolean, default=False)
    correct_termination: Mapped[bool] = mapped_column(Boolean, default=False)
    rude: Mapped[bool] = mapped_column(Boolean, default=False)
    conflict: Mapped[bool] = mapped_column(Boolean, default=False)
    answered_topic: Mapped[bool] = mapped_column(Boolean, default=False)
    toxic: Mapped[bool] = mapped_column(Boolean, default=False)
    violations: Mapped[bool] = mapped_column(Boolean, default=False)
    needs_attention: Mapped[bool] = mapped_column(Boolean, default=False)
    issue_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    manager_comment: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0)
    work_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # New metrics
    request_type: Mapped[str] = mapped_column(String(255), default="Вхідний дзвінок")
    branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    asked_car_body: Mapped[bool] = mapped_column(Boolean, default=False)
    asked_car_year: Mapped[bool] = mapped_column(Boolean, default=False)
    service_booking_date: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_top_100_compliant: Mapped[str] = mapped_column(String(50), default="Ні")
    top_100_non_compliant_recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)
    violations_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    spare_parts: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    call: Mapped["Call"] = relationship(back_populates="ai_analysis")
