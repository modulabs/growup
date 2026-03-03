from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class ScoreEntry(BaseModel):
    legacy_student_id: int
    score: Optional[float] = None
    is_submitted: Optional[bool] = None  # None → auto-detect from score


class ScoreBatchRequest(BaseModel):
    scores: List[ScoreEntry]


class ScoreOut(BaseModel):
    id: str
    quest_id: str
    legacy_student_id: int
    student_name: str = ""
    score: Optional[float] = None
    is_submitted: bool = False

    model_config = {"from_attributes": True}


class StudentScoreRow(BaseModel):
    quest_id: str
    quest_number: int
    quest_type: str
    title: Optional[str] = None
    quest_date: str
    score: Optional[float] = None
    is_submitted: bool = False


class BonusScoreCreate(BaseModel):
    legacy_student_id: int
    score: float
    category: str = ""
    reason: str = ""


class BonusScoreOut(BaseModel):
    id: str
    cached_course_id: int
    legacy_student_id: int
    student_name: str = ""
    score: float
    category: str = ""
    reason: str = ""
    given_by_name: str = ""
    given_at: str = ""

    model_config = {"from_attributes": True}


class CourseScoreSummary(BaseModel):
    legacy_course_id: int
    course_name: str
    scores: List[StudentScoreRow]
    bonus_scores: List[BonusScoreOut] = []
    total_quest_score: float = 0.0
    total_bonus_score: float = 0.0
    total_score: float = 0.0


# ── Rubric evaluation (from Legacy DB) ──


class RubricItemOut(BaseModel):
    rubric_metric: str
    rubric_order: Optional[int] = None
    human_score: Optional[int] = None
    gpt_score: Optional[int] = None
    feedback: Optional[str] = None


class TaskRubricOut(BaseModel):
    task_title: str
    node_schedule_id: Optional[int] = None
    rubric_items: List[RubricItemOut]
    overall_feedback: Optional[str] = None
    total_human: int = 0
    total_gpt: int = 0
    max_score: int = 0


class StudentRubricResponse(BaseModel):
    legacy_course_id: int
    course_name: str
    student_name: str = ""
    tasks: List[TaskRubricOut]
    total_rubric_tasks: int = 0
