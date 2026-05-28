import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Call(Base):
    __tablename__ = "calls"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    gdrive_file_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING_DOWNLOAD")
    manager_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("managers.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    manager: Mapped["Manager | None"] = relationship(back_populates="calls")
    transcript: Mapped["Transcript | None"] = relationship(back_populates="call", uselist=False, cascade="all, delete-orphan")
    ai_analysis: Mapped["AIAnalysis | None"] = relationship(back_populates="call", uselist=False, cascade="all, delete-orphan")
    processing_jobs: Mapped[list["ProcessingJob"]] = relationship(back_populates="call", cascade="all, delete-orphan")
    processing_logs: Mapped[list["ProcessingLog"]] = relationship(back_populates="call", cascade="all, delete-orphan")
