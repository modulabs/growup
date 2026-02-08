from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_student
from app.models.bonus import BonusScore
from app.models.cache import CachedCourse, CachedEnrollment, CachedUser
from app.models.quest import Quest, QuestScore
from app.schemas.course import CourseOut
from app.schemas.score import (
    BonusScoreOut,
    CourseScoreSummary,
    RubricItemOut,
    StudentRubricResponse,
    StudentScoreRow,
    TaskRubricOut,
)
from app.services.legacy_service import (
    get_rubric_scores_for_student,
    get_total_rubric_count,
)

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
    total_quest = 0.0
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
            total_quest += score_val

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

    # Bonus scores
    bonus_result = await db.execute(
        select(BonusScore)
        .where(
            BonusScore.cached_course_id == course_id,
            BonusScore.legacy_student_id == uid,
        )
        .order_by(BonusScore.given_at.desc())
    )
    bonus_items = bonus_result.scalars().all()

    bonus_out: list[BonusScoreOut] = []
    total_bonus = 0.0
    for b in bonus_items:
        total_bonus += float(b.score)
        giver_name = b.given_by_name
        if not giver_name:
            giver = await db.get(CachedUser, b.given_by_legacy_user_id)
            giver_name = giver.name if giver else ""

        bonus_out.append(
            BonusScoreOut(
                id=str(b.id),
                cached_course_id=b.cached_course_id,
                legacy_student_id=b.legacy_student_id,
                score=float(b.score),
                reason=b.reason,
                given_by_name=giver_name,
                given_at=b.given_at.isoformat() if b.given_at else "",
            )
        )

    return CourseScoreSummary(
        legacy_course_id=course_id,
        course_name=course_name,
        scores=rows,
        bonus_scores=bonus_out,
        total_quest_score=total_quest,
        total_bonus_score=total_bonus,
        total_score=total_quest + total_bonus,
    )


@router.get("/courses/{course_id}/rubrics", response_model=StudentRubricResponse)
async def my_rubrics(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_student),
):
    uid = current_user["legacy_user_id"]

    course = await db.get(CachedCourse, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not course.legacy_user_group_id:
        raise HTTPException(
            status_code=400, detail="Course has no legacy user group mapping"
        )

    rows = await get_rubric_scores_for_student(uid, course.legacy_user_group_id)

    tasks_map: dict[str, list] = defaultdict(list)
    overall_map: dict[str, str | None] = {}
    for r in rows:
        title = r.get("task_title", "Unknown")
        tasks_map[title].append(r)
        if r.get("overall_feedback"):
            overall_map[title] = r["overall_feedback"]

    tasks: list[TaskRubricOut] = []
    for title, items in tasks_map.items():
        rubric_items = [
            RubricItemOut(
                rubric_metric=it.get("rubric_metric", ""),
                rubric_order=it.get("rubric_order"),
                human_score=it.get("human_score"),
                gpt_score=it.get("gpt_score"),
                feedback=it.get("rubric_feedback"),
            )
            for it in items
            if it.get("rubric_metric")
        ]
        total_human = sum(i.human_score or 0 for i in rubric_items)
        total_gpt = sum(i.gpt_score or 0 for i in rubric_items)
        tasks.append(
            TaskRubricOut(
                task_title=title,
                rubric_items=rubric_items,
                overall_feedback=overall_map.get(title),
                total_human=total_human,
                total_gpt=total_gpt,
                max_score=len(rubric_items),
            )
        )

    user = await db.get(CachedUser, uid)
    total_rubrics = await get_total_rubric_count(course.legacy_user_group_id)

    return StudentRubricResponse(
        legacy_course_id=course_id,
        course_name=course.name,
        student_name=user.name if user else "",
        tasks=tasks,
        total_rubric_tasks=total_rubrics,
    )
