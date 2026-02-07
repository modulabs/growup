from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CachedUser(Base):
    __tablename__ = "cached_users"

    legacy_user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20), default="")
    role: Mapped[str] = mapped_column(
        String(20), default="student"
    )  # student | facilitator
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class CachedCourse(Base):
    __tablename__ = "cached_courses"

    legacy_course_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    legacy_user_group_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    name: Mapped[str] = mapped_column(String(200))
    cohort: Mapped[str] = mapped_column(String(100), default="")
    category: Mapped[str] = mapped_column(String(50), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class CachedEnrollment(Base):
    __tablename__ = "cached_enrollments"

    legacy_user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    legacy_course_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
