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
    reason: str = ""


class BonusScoreOut(BaseModel):
    id: str
    cached_course_id: int
    legacy_student_id: int
    student_name: str = ""
    score: float
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
