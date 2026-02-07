from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.schemas.auth import CourseInfo, LoginResponse
from app.services import cache_service, legacy_service


async def login(name: str, phone: str, db: AsyncSession) -> Optional[LoginResponse]:
    """Authenticate user via Legacy DB and return JWT."""
    # 1. Verify user exists in Legacy
    legacy_user = await legacy_service.verify_user(name, phone)
    if not legacy_user:
        return None

    user_id = int(legacy_user["user_id"])
    user_name = legacy_user.get("first_name", name)

    # 2. Cache user locally
    await cache_service.sync_user(db, legacy_user)

    # 3. Get user courses from Legacy
    courses_data = await legacy_service.get_user_courses(user_id)

    # 4. Determine role: check is_coach flag from Legacy user, or COACH role in courses
    role = "facilitator" if legacy_user.get("is_coach") else "student"
    active_courses = []
    for c in courses_data:
        if c.get("role") == "COACH":
            role = "facilitator"
        if c.get("is_active"):
            active_courses.append(
                CourseInfo(
                    legacy_course_id=int(c.get("user_group_id", 0)),
                    name=c.get("user_group_name", ""),
                )
            )

    # 5. Create JWT
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
