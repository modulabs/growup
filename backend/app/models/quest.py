from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Quest(Base):
    __tablename__ = "quests"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    cached_course_id: Mapped[int] = mapped_column(BigInteger, index=True)
    quest_number: Mapped[int]
    quest_type: Mapped[str] = mapped_column(
        String(20)
    )  # sub | main | datathon | ideathon
    module_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quest_date: Mapped[date] = mapped_column(Date)
    created_by_legacy_user_id: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class QuestScore(Base):
    __tablename__ = "quest_scores"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    quest_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    legacy_student_id: Mapped[int] = mapped_column(BigInteger, index=True)
    score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1), nullable=True)
    is_submitted: Mapped[bool] = mapped_column(Boolean, default=False)
    graded_by_legacy_user_id: Mapped[int] = mapped_column(BigInteger)
    graded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
