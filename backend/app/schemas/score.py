from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class ScoreEntry(BaseModel):
    legacy_student_id: int
    score: Optional[float] = None
    is_submitted: bool = False


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


class CourseScoreSummary(BaseModel):
    legacy_course_id: int
    course_name: str
    scores: List[StudentScoreRow]
    total_score: float = 0.0
