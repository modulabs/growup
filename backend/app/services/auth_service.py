from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.override import FacilitatorOverride
from app.schemas.auth import CourseInfo, LoginResponse
from app.services import cache_service, legacy_service


async def _is_facilitator_override(db: AsyncSession, legacy_user_id: int) -> bool:
    """Check if user has a manual facilitator override."""
    result = await db.execute(
        select(FacilitatorOverride).where(
            FacilitatorOverride.legacy_user_id == legacy_user_id
        )
    )
    return result.scalar_one_or_none() is not None


async def login(email: str, phone: str, db: AsyncSession) -> Optional[LoginResponse]:
    """Authenticate user via Legacy DB and return JWT.
      1. facilitator_overrides table (manual override)
      2. Legacy DB is_coach flag
      3. COACH role in any active course
    4. Default: student
    Security: Facilitators MUST append 'Facil' to their phone number.
    """
    # 0. Detect Facil suffix (facilitator security keyword)
    FACIL_SUFFIX = "Facil"
    facil_requested = phone.endswith(FACIL_SUFFIX)
    clean_phone = phone[: -len(FACIL_SUFFIX)] if facil_requested else phone
    # 1. Verify user exists in Legacy
    legacy_user = await legacy_service.verify_user(email, clean_phone)
    if not legacy_user:
        return None

    user_id = int(legacy_user["user_id"])
    user_name = legacy_user.get("first_name") or ""

    # 2. Cache user locally
    await cache_service.sync_user(db, legacy_user)

    # 3. Get user courses from Legacy
    courses_data = await legacy_service.get_user_courses(user_id)

    # 4. Determine role
    # Priority 1: Check facilitator override table
    if await _is_facilitator_override(db, user_id):
        role = "facilitator"
    # Priority 2: Check Legacy is_coach flag
    elif legacy_user.get("is_coach"):
        role = "facilitator"
    else:
        # Priority 3: Check if COACH in any course
        role = "student"
        for c in courses_data:
            if c.get("role") == "COACH":
                role = "facilitator"
                break


    # 4b. Facilitator security: require 'Facil' suffix
    if role == "facilitator" and not facil_requested:
        # Facilitator must provide the suffix — deny access
        return None
    if facil_requested and role != "facilitator":
        # Non-facilitator provided 'Facil' suffix — deny access
        return None
    active_courses = []
    for c in courses_data:
        if c.get("is_active"):
            active_courses.append(
                CourseInfo(
                    legacy_course_id=int(c.get("user_group_id", 0)),
                    name=c.get("user_group_name", ""),
                )
            )

    # 5. Commit cached user to DB (sync_user only flushes)
    await db.commit()

    # 6. Create JWT
    token = create_access_token(
        {
            "sub": str(user_id),
            "legacy_user_id": user_id,
            "name": user_name,
            "role": role,
        }
    )

    return LoginResponse(
        access_token=token,
        legacy_user_id=user_id,
        name=user_name,
        role=role,
        active_courses=active_courses,
    )
