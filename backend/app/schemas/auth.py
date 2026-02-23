from __future__ import annotations

from typing import List

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    phone: str


class CourseInfo(BaseModel):
    legacy_course_id: int
    name: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    legacy_user_id: int
    name: str
    role: str  # student | facilitator
    active_courses: List[CourseInfo]
