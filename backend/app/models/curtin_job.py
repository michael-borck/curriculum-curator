"""SQLAlchemy model tracking Blackboard course-archive export jobs."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.common import GUID


class CurtinExportJob(Base):
    __tablename__ = "curtin_export_jobs"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    user_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    course_name: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(
        String(20), default="triggered"
    )  # triggered | downloaded | failed
    triggered_at: Mapped[datetime] = mapped_column(default=func.now())
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
