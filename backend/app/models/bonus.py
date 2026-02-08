from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Numeric, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BonusScore(Base):
    __tablename__ = "bonus_scores"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    cached_course_id: Mapped[int] = mapped_column(BigInteger, index=True)
    legacy_student_id: Mapped[int] = mapped_column(BigInteger, index=True)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 1))
    reason: Mapped[str] = mapped_column(Text, default="")
    given_by_legacy_user_id: Mapped[int] = mapped_column(BigInteger)
    given_by_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    given_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
