from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_facilitator
from app.models.bonus import BonusScore
from app.models.cache import CachedCourse, CachedEnrollment, CachedUser
from app.models.favorite import FacilitatorFavorite
from app.models.quest import Quest, QuestScore
from app.schemas.course import CourseOut, StudentOut
from app.schemas.quest import (
    BatchDeleteRequest,
    QuestCreate,
    QuestOut,
    QuestUpdate,
    SheetImportRequest,
    SheetImportResponse,
)
from app.schemas.score import (
    BonusScoreCreate,
    BonusScoreOut,
    RubricItemOut,
    ScoreBatchRequest,
    ScoreOut,
    StudentRubricResponse,
    TaskRubricOut,
)
from app.services.legacy_service import get_rubric_scores_for_student
from app.services.sheet_service import import_from_sheet

router = APIRouter(tags=["facilitator"])

# ── Score validation rules per quest type ──
SCORE_RULES: dict[str, dict] = {
    "sub": {"min": 0, "max": 1, "step": 1},
    "main": {"min": 0, "max": 5, "step": 1},
    "datathon": {"min": 0, "max": 10, "step": 0.5},
    "ideathon": {"min": 0, "max": 20, "step": 0.5},
}


def _validate_score(quest_type: str, score: float | None, is_submitted: bool) -> None:
    if not is_submitted and score is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Score must be null when is_submitted is False",
        )
    if not is_submitted:
        return
    if score is None:
        # submitted but no score yet is allowed (graded later)
        return
    rules = SCORE_RULES.get(quest_type)
    if not rules:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown quest type: {quest_type}",
        )
    if score < rules["min"] or score > rules["max"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Score for {quest_type} must be between {rules['min']} and {rules['max']}",
        )
    step = rules["step"]
    if step == 1 and score != int(score):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Score for {quest_type} must be an integer",
        )
    if step == 0.5 and (score * 2) != int(score * 2):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Score for {quest_type} must be in 0.5 increments",
        )


# ── Courses ──


@router.get("/courses", response_model=list[CourseOut])
async def list_courses(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_facilitator),
):
    fac_id = current_user["legacy_user_id"]
    courses_result = await db.execute(
        select(CachedCourse).where(CachedCourse.is_active.is_(True))
    )
    courses = courses_result.scalars().all()

    # Get favorites for this facilitator
    fav_result = await db.execute(
        select(FacilitatorFavorite.cached_course_id).where(
            FacilitatorFavorite.legacy_facilitator_id == fac_id
        )
    )
    fav_ids = {r for r in fav_result.scalars().all()}

    return [
        CourseOut(
            legacy_course_id=c.legacy_course_id,
            legacy_user_group_id=c.legacy_user_group_id,
            name=c.name,
            cohort=c.cohort,
            category=c.category,
            is_active=c.is_active,
            is_favorite=c.legacy_course_id in fav_ids,
        )
        for c in courses
    ]


@router.get("/courses/{course_id}/students", response_model=list[StudentOut])
async def list_students(
    course_id: int,
    active: bool | None = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_facilitator),
):
    stmt = (
        select(CachedUser, CachedEnrollment.is_active)
        .join(
            CachedEnrollment,
            CachedEnrollment.legacy_user_id == CachedUser.legacy_user_id,
        )
        .where(CachedEnrollment.legacy_course_id == course_id)
        .where(CachedUser.name != "")
        .order_by(CachedUser.name)
    )
    if active is not None:
        stmt = stmt.where(CachedEnrollment.is_active.is_(active))
    result = await db.execute(stmt)
    return [
        StudentOut(
            legacy_user_id=user.legacy_user_id,
            name=user.name,
            is_active=enrollment_active,
        )
        for user, enrollment_active in result.all()
    ]


@router.patch("/courses/{course_id}/students/{student_id}/active")
async def toggle_student_active(
    course_id: int,
    student_id: int,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_facilitator),
):
    enrollment = await db.get(CachedEnrollment, (student_id, course_id))
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    enrollment.is_active = not enrollment.is_active
    await db.commit()
    return {"legacy_user_id": student_id, "is_active": enrollment.is_active}

# ── Quests ──


@router.get("/quests/{quest_id}", response_model=QuestOut)
async def get_quest(
    quest_id: str,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_facilitator),
):
    quest = await db.get(Quest, quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")

    total_stmt = select(func.count()).where(
        CachedEnrollment.legacy_course_id == quest.cached_course_id
    ).where(CachedEnrollment.is_active.is_(True))
    total_students = (await db.execute(total_stmt)).scalar() or 0

    graded_stmt = (
        select(func.count())
        .where(QuestScore.quest_id == quest.id)
        .where(QuestScore.is_submitted.is_(True))
    )
    graded_count = (await db.execute(graded_stmt)).scalar() or 0

    return QuestOut(
        id=str(quest.id),
        cached_course_id=quest.cached_course_id,
        quest_number=quest.quest_number,
        quest_type=quest.quest_type,
        title=quest.title,
        quest_date=quest.quest_date,
        graded_count=graded_count,
        total_students=total_students,
    )


@router.get("/courses/{course_id}/quests", response_model=list[QuestOut])
async def list_quests(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_facilitator),
):
    quests_result = await db.execute(
        select(Quest)
        .where(Quest.cached_course_id == course_id)
        .order_by(Quest.quest_number)
    )
    quests = quests_result.scalars().all()

    # Count total students for this course
    total_stmt = select(func.count()).where(
        CachedEnrollment.legacy_course_id == course_id
    ).where(CachedEnrollment.is_active.is_(True))
    total_students = (await db.execute(total_stmt)).scalar() or 0

    out = []
    for q in quests:
        graded_stmt = (
            select(func.count())
            .where(QuestScore.quest_id == q.id)
            .where(QuestScore.is_submitted.is_(True))
        )
        graded_count = (await db.execute(graded_stmt)).scalar() or 0
        out.append(
            QuestOut(
                id=str(q.id),
                cached_course_id=q.cached_course_id,
                quest_number=q.quest_number,
                quest_type=q.quest_type,
                title=q.title,
                quest_date=q.quest_date,
                graded_count=graded_count,
                total_students=total_students,
            )
        )
    return out


@router.post("/courses/{course_id}/quests", response_model=QuestOut, status_code=201)
async def create_quest(
    course_id: int,
    body: QuestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_facilitator),
):
    quest = Quest(
        cached_course_id=course_id,
        quest_number=body.quest_number,
        quest_type=body.quest_type,
        title=body.title,
        quest_date=body.quest_date,
        created_by_legacy_user_id=current_user["legacy_user_id"],
    )
    db.add(quest)
    await db.commit()
    await db.refresh(quest)

    return QuestOut(
        id=str(quest.id),
        cached_course_id=quest.cached_course_id,
        quest_number=quest.quest_number,
        quest_type=quest.quest_type,
        title=quest.title,
        quest_date=quest.quest_date,
        graded_count=0,
        total_students=0,
    )


@router.put("/quests/{quest_id}", response_model=QuestOut)
async def update_quest(
    quest_id: str,
    body: QuestUpdate,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_facilitator),
):
    quest = await db.get(Quest, quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(quest, field, value)
    await db.commit()
    await db.refresh(quest)

    return QuestOut(
        id=str(quest.id),
        cached_course_id=quest.cached_course_id,
        quest_number=quest.quest_number,
        quest_type=quest.quest_type,
        title=quest.title,
        quest_date=quest.quest_date,
    )


@router.delete("/quests/{quest_id}", status_code=204)
async def delete_quest(
    quest_id: str,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_facilitator),
):
    quest = await db.get(Quest, quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")

    # Delete associated scores first
    await db.execute(delete(QuestScore).where(QuestScore.quest_id == quest_id))
    await db.delete(quest)
    await db.commit()


@router.delete("/courses/{course_id}/quests", status_code=200)
async def delete_all_course_quests(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_facilitator),
):
    """Delete ALL quests (and their scores) for a course."""
    # Get all quest ids for this course
    quest_ids_result = await db.execute(
        select(Quest.id).where(Quest.cached_course_id == course_id)
    )
    quest_ids = [str(qid) for qid in quest_ids_result.scalars().all()]

    if not quest_ids:
        return {"deleted_count": 0}

    # Delete scores first, then quests
    await db.execute(delete(QuestScore).where(QuestScore.quest_id.in_(quest_ids)))
    await db.execute(delete(Quest).where(Quest.cached_course_id == course_id))
    await db.commit()

    return {"deleted_count": len(quest_ids)}


@router.post("/courses/{course_id}/quests/batch-delete", status_code=200)
async def batch_delete_quests(
    course_id: int,
    body: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_facilitator),
):
    """Delete selected quests (and their scores) by IDs."""
    if not body.quest_ids:
        return {"deleted_count": 0}

    # Verify all quests belong to this course
    verify_result = await db.execute(
        select(Quest.id)
        .where(Quest.id.in_(body.quest_ids))
        .where(Quest.cached_course_id == course_id)
    )
    valid_ids = [str(qid) for qid in verify_result.scalars().all()]

    if not valid_ids:
        return {"deleted_count": 0}

    # Delete scores first, then quests
    await db.execute(delete(QuestScore).where(QuestScore.quest_id.in_(valid_ids)))
    await db.execute(delete(Quest).where(Quest.id.in_(valid_ids)))
    await db.commit()

    return {"deleted_count": len(valid_ids)}


# ── Scores ──


@router.get("/quests/{quest_id}/students", response_model=list[ScoreOut])
async def list_quest_students(
    quest_id: str,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_facilitator),
):
    quest = await db.get(Quest, quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")

    # Get all enrolled students for this course
    students_stmt = (
        select(CachedUser)
        .join(
            CachedEnrollment,
            CachedEnrollment.legacy_user_id == CachedUser.legacy_user_id,
        )
        .where(CachedEnrollment.legacy_course_id == quest.cached_course_id)
        .where(CachedEnrollment.is_active.is_(True))
        .where(CachedUser.name != "")
        .order_by(CachedUser.name)
    )
    students_result = await db.execute(students_stmt)
    students = students_result.scalars().all()

    # Get existing scores
    scores_result = await db.execute(
        select(QuestScore).where(QuestScore.quest_id == quest_id)
    )
    score_map = {s.legacy_student_id: s for s in scores_result.scalars().all()}

    out = []
    for stu in students:
        existing = score_map.get(stu.legacy_user_id)
        if existing:
            out.append(
                ScoreOut(
                    id=str(existing.id),
                    quest_id=quest_id,
                    legacy_student_id=stu.legacy_user_id,
                    student_name=stu.name,
                    score=float(existing.score) if existing.score is not None else None,
                    is_submitted=existing.is_submitted,
                )
            )
        else:
            out.append(
                ScoreOut(
                    id="",
                    quest_id=quest_id,
                    legacy_student_id=stu.legacy_user_id,
                    student_name=stu.name,
                    score=None,
                    is_submitted=False,
                )
            )
    return out


@router.post("/quests/{quest_id}/scores", response_model=list[ScoreOut])
async def batch_upsert_scores(
    quest_id: str,
    body: ScoreBatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_facilitator),
):
    quest = await db.get(Quest, quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")

    grader_id = current_user["legacy_user_id"]
    now = datetime.now(timezone.utc)
    results = []

    for entry in body.scores:
        # Auto-detect is_submitted if not explicitly provided
        is_submitted = entry.is_submitted
        if is_submitted is None:
            is_submitted = entry.score is not None

        # Validate
        _validate_score(quest.quest_type, entry.score, is_submitted)

        # Find existing score
        stmt = select(QuestScore).where(
            QuestScore.quest_id == quest_id,
            QuestScore.legacy_student_id == entry.legacy_student_id,
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        score_decimal = Decimal(str(entry.score)) if entry.score is not None else None

        if existing:
            existing.score = score_decimal
            existing.is_submitted = is_submitted
            existing.graded_by_legacy_user_id = grader_id
            existing.graded_at = now
            await db.flush()
            obj = existing
        else:
            obj = QuestScore(
                quest_id=quest_id,
                legacy_student_id=entry.legacy_student_id,
                score=score_decimal,
                is_submitted=is_submitted,
                graded_by_legacy_user_id=grader_id,
                graded_at=now,
            )
            db.add(obj)
            await db.flush()
            await db.refresh(obj)

        # Get student name
        stu = await db.get(CachedUser, entry.legacy_student_id)
        student_name = stu.name if stu else ""

        results.append(
            ScoreOut(
                id=str(obj.id),
                quest_id=quest_id,
                legacy_student_id=entry.legacy_student_id,
                student_name=student_name,
                score=float(obj.score) if obj.score is not None else None,
                is_submitted=obj.is_submitted,
            )
        )

    await db.commit()
    return results


# ── Bonus Scores ──


@router.get("/courses/{course_id}/bonus-scores", response_model=list[BonusScoreOut])
async def list_bonus_scores(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_facilitator),
):
    stmt = (
        select(BonusScore)
        .where(BonusScore.cached_course_id == course_id)
        .order_by(BonusScore.given_at.desc())
    )
    result = await db.execute(stmt)
    items = result.scalars().all()

    out = []
    for b in items:
        stu = await db.get(CachedUser, b.legacy_student_id)
        giver = await db.get(CachedUser, b.given_by_legacy_user_id)
        out.append(
            BonusScoreOut(
                id=str(b.id),
                cached_course_id=b.cached_course_id,
                legacy_student_id=b.legacy_student_id,
                student_name=stu.name if stu else "",
                score=float(b.score),
                category=b.category,
                reason=b.reason,
                given_by_name=b.given_by_name or (giver.name if giver else ""),
                given_at=b.given_at.isoformat() if b.given_at else "",
            )
        )
    return out


@router.post(
    "/courses/{course_id}/bonus-scores", response_model=BonusScoreOut, status_code=201
)
async def create_bonus_score(
    course_id: int,
    body: BonusScoreCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_facilitator),
):
    bonus = BonusScore(
        cached_course_id=course_id,
        legacy_student_id=body.legacy_student_id,
        score=Decimal(str(body.score)),
        category=body.category,
        reason=body.reason,
        given_by_legacy_user_id=current_user["legacy_user_id"],
        given_by_name=current_user["name"],
    )
    db.add(bonus)
    await db.commit()
    await db.refresh(bonus)

    stu = await db.get(CachedUser, bonus.legacy_student_id)
    giver = await db.get(CachedUser, bonus.given_by_legacy_user_id)
    return BonusScoreOut(
        id=str(bonus.id),
        cached_course_id=bonus.cached_course_id,
        legacy_student_id=bonus.legacy_student_id,
        student_name=stu.name if stu else "",
        score=float(bonus.score),
        category=bonus.category,
        reason=bonus.reason,
        given_by_name=bonus.given_by_name,
        given_at=bonus.given_at.isoformat() if bonus.given_at else "",
    )


@router.delete("/bonus-scores/{bonus_id}", status_code=204)
async def delete_bonus_score(
    bonus_id: str,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_facilitator),
):
    bonus = await db.get(BonusScore, bonus_id)
    if not bonus:
        raise HTTPException(status_code=404, detail="Bonus score not found")
    await db.delete(bonus)
    await db.commit()


# ── Favorites ──


@router.post("/courses/{course_id}/favorite")
async def toggle_favorite(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_facilitator),
):
    fac_id = current_user["legacy_user_id"]
    stmt = select(FacilitatorFavorite).where(
        FacilitatorFavorite.legacy_facilitator_id == fac_id,
        FacilitatorFavorite.cached_course_id == course_id,
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        await db.delete(existing)
        await db.commit()
        return {"is_favorite": False}
    else:
        fav = FacilitatorFavorite(
            legacy_facilitator_id=fac_id,
            cached_course_id=course_id,
        )
        db.add(fav)
        await db.commit()
        return {"is_favorite": True}


@router.get(
    "/courses/{course_id}/students/{student_id}/rubrics",
    response_model=StudentRubricResponse,
)
async def student_rubrics(
    course_id: int,
    student_id: int,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_facilitator),
):
    course = await db.get(CachedCourse, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not course.legacy_user_group_id:
        raise HTTPException(
            status_code=400, detail="Course has no legacy user group mapping"
        )

    rows = await get_rubric_scores_for_student(student_id, course.legacy_user_group_id)

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

    user = await db.get(CachedUser, student_id)
    return StudentRubricResponse(
        legacy_course_id=course_id,
        course_name=course.name,
        student_name=user.name if user else "",
        tasks=tasks,
    )


# ── Sheet Import ──


@router.post("/courses/{course_id}/import-sheet", response_model=SheetImportResponse)
async def import_sheet(
    course_id: int,
    body: SheetImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_facilitator),
):
    result = await import_from_sheet(
        db=db,
        spreadsheet_id=body.spreadsheet_id,
        course_id=course_id,
        facilitator_id=current_user["legacy_user_id"],
        sheet_name=body.sheet_name,
    )
    return SheetImportResponse(
        quests_created=result.quests_created,
        quests_updated=result.quests_updated,
        scores_created=result.scores_created,
        scores_updated=result.scores_updated,
        students_matched=result.students_matched,
        students_unmatched=result.students_unmatched,
        errors=result.errors,
    )
