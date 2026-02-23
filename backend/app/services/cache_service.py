from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cache import CachedCourse, CachedEnrollment, CachedUser
from app.services import legacy_service

logger = logging.getLogger(__name__)


async def sync_user(db: AsyncSession, legacy_user: dict) -> CachedUser:
    """Upsert a user into the cache from Legacy data."""
    user_id = int(legacy_user["user_id"])
    existing = await db.get(CachedUser, user_id)
    if existing:
        existing.name = legacy_user.get("first_name", existing.name)
        existing.phone = legacy_user.get("phone_number", existing.phone)
        existing.last_synced_at = datetime.now(timezone.utc)
        await db.flush()
        return existing
    new_user = CachedUser(
        legacy_user_id=user_id,
        name=legacy_user.get("first_name", ""),
        phone=legacy_user.get("phone_number", ""),
        role="facilitator" if legacy_user.get("is_coach") else "student",
        last_synced_at=datetime.now(timezone.utc),
    )
    db.add(new_user)
    await db.flush()
    return new_user


async def sync_courses(db: AsyncSession) -> list[CachedCourse]:
    """Sync all active courses from Legacy DB into cache."""
    rows = await legacy_service.list_active_courses()
    synced = []
    for row in rows:
        ug_id = row.get("user_group_id")
        if not ug_id:
            continue
        ug_id = int(ug_id)
        existing = await db.execute(
            select(CachedCourse).where(CachedCourse.legacy_user_group_id == ug_id)
        )
        course = existing.scalar_one_or_none()
        if course:
            course.name = row.get("user_group_name", course.name)
            course.is_active = row.get("is_active", True)
            course.last_synced_at = datetime.now(timezone.utc)
        else:
            course = CachedCourse(
                legacy_course_id=ug_id,
                legacy_user_group_id=ug_id,
                name=row.get("user_group_name", ""),
                cohort=row.get("user_group_name", ""),
                is_active=row.get("is_active", True),
                last_synced_at=datetime.now(timezone.utc),
            )
            db.add(course)
        synced.append(course)
    await db.commit()
    return synced


async def sync_students_for_course(
    db: AsyncSession, user_group_id: int
) -> list[CachedUser]:
    rows = await legacy_service.list_students_by_course(user_group_id)
    active_user_ids = set()
    synced = []
    for row in rows:
        uid = row.get("user_id")
        name = (row.get("name") or "").strip()
        if not uid or not name:
            continue
        uid = int(uid)
        active_user_ids.add(uid)
        existing = await db.get(CachedUser, uid)
        if existing:
            existing.name = row.get("name", existing.name)
            existing.role = "student"
            existing.last_synced_at = datetime.now(timezone.utc)
        else:
            existing = CachedUser(
                legacy_user_id=uid,
                name=row.get("name", ""),
                role="student",
                last_synced_at=datetime.now(timezone.utc),
            )
            db.add(existing)
        synced.append(existing)
        enrollment_exists = await db.get(CachedEnrollment, (uid, user_group_id))
        if not enrollment_exists:
            db.add(CachedEnrollment(legacy_user_id=uid, legacy_course_id=user_group_id))

    existing_enrollments = await db.execute(
        select(CachedEnrollment).where(
            CachedEnrollment.legacy_course_id == user_group_id
        )
    )
    for enrollment in existing_enrollments.scalars().all():
        if enrollment.legacy_user_id not in active_user_ids:
            enrollment.is_active = False
        else:
            enrollment.is_active = True

    await db.commit()
    return synced
