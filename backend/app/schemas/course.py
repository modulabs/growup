from __future__ import annotations

from pydantic import BaseModel


class CourseOut(BaseModel):
    legacy_course_id: int
    legacy_user_group_id: int | None = None
    name: str
    cohort: str = ""
    category: str = ""
    is_active: bool = True
    is_favorite: bool = False

    model_config = {"from_attributes": True}


class StudentOut(BaseModel):
    legacy_user_id: int
    name: str

    model_config = {"from_attributes": True}
