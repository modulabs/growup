from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_student
from app.models.cache import CachedCourse, CachedEnrollment
from app.models.quest import Quest, QuestScore
from app.schemas.course import CourseOut
from app.schemas.score import CourseScoreSummary, StudentScoreRow

router = APIRouter(tags=["student"])


@router.get("/courses", response_model=list[CourseOut])
async def list_my_courses(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_student),
):
    uid = current_user["legacy_user_id"]
    stmt = (
        select(CachedCourse)
        .join(
            CachedEnrollment,
            CachedEnrollment.legacy_course_id == CachedCourse.legacy_course_id,
        )
        .where(CachedEnrollment.legacy_user_id == uid)
    )
    result = await db.execute(stmt)
    courses = result.scalars().all()
    return [CourseOut.model_validate(c) for c in courses]


@router.get("/courses/{course_id}/scores", response_model=CourseScoreSummary)
async def my_scores(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_student),
):
    uid = current_user["legacy_user_id"]

    # Get course name
    course = await db.get(CachedCourse, course_id)
    course_name = course.name if course else ""

    # Get all quests for this course
    quests_result = await db.execute(
        select(Quest)
        .where(Quest.cached_course_id == course_id)
        .order_by(Quest.quest_number)
    )
    quests = quests_result.scalars().all()

    rows: list[StudentScoreRow] = []
    total = 0.0
    for q in quests:
        score_result = await db.execute(
            select(QuestScore).where(
                QuestScore.quest_id == q.id,
                QuestScore.legacy_student_id == uid,
            )
        )
        qs = score_result.scalar_one_or_none()
        score_val = float(qs.score) if qs and qs.score is not None else None
        is_sub = qs.is_submitted if qs else False

        if score_val is not None:
            total += score_val

        rows.append(
            StudentScoreRow(
                quest_id=str(q.id),
                quest_number=q.quest_number,
                quest_type=q.quest_type,
                title=q.title,
                quest_date=str(q.quest_date),
                score=score_val,
                is_submitted=is_sub,
            )
        )

    return CourseScoreSummary(
        legacy_course_id=course_id,
        course_name=course_name,
        scores=rows,
        total_score=total,
    )
