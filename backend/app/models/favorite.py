from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FacilitatorFavorite(Base):
    __tablename__ = "facilitator_favorites"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    legacy_facilitator_id: Mapped[int] = mapped_column(BigInteger, index=True)
    cached_course_id: Mapped[int] = mapped_column(BigInteger)
