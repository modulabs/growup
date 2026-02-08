from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel


class QuestCreate(BaseModel):
    quest_number: int
    quest_type: str  # sub | main | datathon | ideathon
    title: Optional[str] = None
    quest_date: date


class QuestUpdate(BaseModel):
    quest_number: Optional[int] = None
    quest_type: Optional[str] = None
    title: Optional[str] = None
    quest_date: Optional[date] = None


class QuestOut(BaseModel):
    id: str
    cached_course_id: int
    quest_number: int
    quest_type: str
    title: Optional[str] = None
    quest_date: date
    graded_count: int = 0
    total_students: int = 0

    model_config = {"from_attributes": True}


class BatchDeleteRequest(BaseModel):
    quest_ids: list[str]


class SheetImportRequest(BaseModel):
    spreadsheet_id: str
    sheet_name: str = "퀘스트"


class SheetImportResponse(BaseModel):
    quests_created: int = 0
    quests_updated: int = 0
    scores_created: int = 0
    scores_updated: int = 0
    errors: list[str] = []
