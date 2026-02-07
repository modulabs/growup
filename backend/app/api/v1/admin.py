from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_facilitator
from app.services import cache_service

router = APIRouter(tags=["admin"])


@router.post("/sync/courses")
async def sync_courses(
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_facilitator),
):
    courses = await cache_service.sync_courses(db)
    return {"synced": len(courses)}


@router.post("/sync/students/{course_id}")
async def sync_students(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_facilitator),
):
    students = await cache_service.sync_students_for_course(db, course_id)
    return {"synced": len(students)}
