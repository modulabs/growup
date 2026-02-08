from __future__ import annotations

import base64
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

TIMEOUT = 15.0


def _build_auth_headers() -> Dict[str, str]:
    """Build HTTP Basic Auth header for n8n webhook."""
    user = settings.N8N_LEGACY_DB_AUTH_USER
    passwd = settings.N8N_LEGACY_DB_AUTH_PASS
    if not user:
        return {}
    token = base64.b64encode(f"{user}:{passwd}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


async def _query_legacy(sql: str) -> List[Dict[str, Any]]:
    """Execute a SQL query against Legacy DB via n8n webhook."""
    if not settings.N8N_LEGACY_DB_WEBHOOK_URL:
        logger.warning("N8N_LEGACY_DB_WEBHOOK_URL not configured")
        return []
    headers = _build_auth_headers()
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            settings.N8N_LEGACY_DB_WEBHOOK_URL,
            json={"query": sql},
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data
        return []


async def verify_user(name: str, phone: str) -> Optional[Dict[str, Any]]:
    """Verify user by name + phone against Legacy DB.
    Returns dict with user_id, first_name, phone_number, roles list, or None."""
    sql = f"""
    SELECT
        cu.id AS user_id,
        cu.first_name,
        cup.phone_number,
        cu.is_coach,
        cu.is_student
    FROM core_user cu
    JOIN core_userprivacy cup ON cu.id = cup.user_id
    WHERE TRIM(cu.first_name) = '{name.strip()}'
      AND REPLACE(cup.phone_number, '-', '') = '{phone.replace("-", "").strip()}'
    ORDER BY cu.id DESC
    LIMIT 1
    """
    rows = await _query_legacy(sql)
    if not rows:
        return None
    return rows[0]


async def get_user_courses(user_id: int) -> List[Dict[str, Any]]:
    """Get courses the user is enrolled in (active semesters)."""
    sql = f"""
    SELECT
        ug.id AS user_group_id,
        ug.name AS user_group_name,
        ugm.role,
        acs.id AS course_semester_id,
        acs.is_active
    FROM user_group_mapping ugm
    JOIN user_group ug ON ugm.user_group_id = ug.id
    LEFT JOIN apply_coursesemester acs ON ug.course_semester_id = acs.id
    WHERE ugm.user_id = {user_id}
    ORDER BY acs.is_active DESC, ug.name
    """
    return await _query_legacy(sql)


async def list_active_courses() -> List[Dict[str, Any]]:
    """List all active courses (user_groups with active semesters)."""
    sql = """
    SELECT
        ug.id AS user_group_id,
        ug.name AS user_group_name,
        acs.id AS course_semester_id,
        acs.is_active
    FROM user_group ug
    LEFT JOIN apply_coursesemester acs ON ug.course_semester_id = acs.id
    WHERE acs.is_active = true
    ORDER BY ug.name
    """
    return await _query_legacy(sql)


async def list_students_by_course(user_group_id: int) -> List[Dict[str, Any]]:
    """List students enrolled in a specific course (user_group)."""
    sql = f"""
    SELECT
        cu.id AS user_id,
        cu.first_name AS name,
        ugm.role
    FROM user_group_mapping ugm
    JOIN core_user cu ON ugm.user_id = cu.id
    WHERE ugm.user_group_id = {user_group_id}
      AND ugm.role = 'MEMBER'
      AND TRIM(COALESCE(cu.first_name, '')) != ''
    ORDER BY cu.first_name
    """
    return await _query_legacy(sql)
