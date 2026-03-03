from __future__ import annotations

import base64
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

TIMEOUT = 15.0
_NODESCHEDULE_TIME_COLUMN_CANDIDATES = (
    "scheduled_at",
    "schedule_at",
    "start_at",
    "started_at",
    "start_date",
    "scheduled_date",
    "lesson_date",
    "date",
    "created_at",
)
_nodeschedule_time_column: Optional[str] = None
_nodeschedule_time_checked = False


def _sql_escape(value: str) -> str:
    return value.replace("'", "''")


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


async def _resolve_nodeschedule_time_column() -> Optional[str]:
    global _nodeschedule_time_checked, _nodeschedule_time_column

    if _nodeschedule_time_checked:
        return _nodeschedule_time_column

    rows = await _query_legacy(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'core_nodeschedule'
        """
    )
    available = {str(row.get("column_name", "")).lower() for row in rows}

    for candidate in _NODESCHEDULE_TIME_COLUMN_CANDIDATES:
        if candidate in available:
            _nodeschedule_time_column = candidate
            break

    _nodeschedule_time_checked = True
    return _nodeschedule_time_column


async def verify_user(email: str, phone: str) -> Optional[Dict[str, Any]]:
    email_norm = _sql_escape(email.strip().lower())
    phone_norm = _sql_escape(phone.replace("-", "").strip())
    sql = f"""
    SELECT
        cu.id AS user_id,
        cu.first_name,
        cup.phone_number,
        cu.is_coach,
        cu.is_student
    FROM core_user cu
    JOIN core_userprivacy cup ON cu.id = cup.user_id
    WHERE LOWER(TRIM(cu.email)) = '{email_norm}'
      AND REPLACE(cup.phone_number, '-', '') = '{phone_norm}'
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


async def get_rubric_scores_for_student(
    user_id: int, user_group_id: int
) -> List[Dict[str, Any]]:
    """Fetch rubric evaluation results for a specific student in a course.

    Returns rows with: task_title, node_schedule_id, rubric_metric, rubric_order,
    human_score, gpt_score, rubric_feedback, overall_feedback
    """
    # 1. Get course IDs for this group (optimization)
    sql_courses = f"SELECT course_id FROM user_group_course_mapping WHERE user_group_id = {user_group_id}"
    courses = await _query_legacy(sql_courses)
    if not courses:
        return []
    course_ids = [str(c["course_id"]) for c in courses]
    course_ids_str = ", ".join(course_ids)

    node_schedule_time_column = await _resolve_nodeschedule_time_column()
    node_schedule_at_select = (
        f",\n        ns.{node_schedule_time_column} AS node_schedule_at"
        if node_schedule_time_column
        else ""
    )
    order_by_clause = (
        f"ORDER BY ns.{node_schedule_time_column} NULLS LAST, ns.id, r.\"order\", n.title"
        if node_schedule_time_column
        else 'ORDER BY ns.id, r."order", n.title'
    )

    sql = f"""
    SELECT
        n.title AS task_title,
        ns.id AS node_schedule_id,
        r.metric AS rubric_metric,
        r."order" AS rubric_order,
        e.score AS human_score,
        rge.gpt_score,
        rge.gpt_comment AS rubric_feedback,
        ge.overall_comment AS overall_feedback{node_schedule_at_select}
    FROM core_evaluation e
    JOIN core_nodeprogrs np ON e.node_progrs_id = np.id
    JOIN core_nodeschedule ns ON np.node_schedule_id = ns.id
    JOIN core_node n ON ns.node_id = n.id
    JOIN core_nodeversion nv ON ns.node_version_id = nv.id
    JOIN core_coursenodeversionrelation cnvr ON nv.id = cnvr.node_version_id
    JOIN core_userenrolments ue ON np.user_enrolments_id = ue.id
    LEFT JOIN core_gptevaluation ge ON ge.node_progrs_id = np.id
    LEFT JOIN core_rubric r ON e.rubric_id = r.id
    LEFT JOIN core_rubricgptevaluation rge ON rge.evaluation_id = e.id
    WHERE ue.user_id = {user_id}
      AND cnvr.course_id IN ({course_ids_str})
    {order_by_clause}
    """
    return await _query_legacy(sql)


async def get_rubric_scores_all_students(
    user_group_id: int,
) -> List[Dict[str, Any]]:
    """Fetch rubric evaluation results for ALL students in a course.

    Returns rows with: student_id, student_name, task_title, node_schedule_id, rubric_metric,
    rubric_order, human_score, gpt_score, rubric_feedback, overall_feedback
    """
    # 1. Get course IDs for this group (optimization)
    sql_courses = f"SELECT course_id FROM user_group_course_mapping WHERE user_group_id = {user_group_id}"
    courses = await _query_legacy(sql_courses)
    if not courses:
        return []
    course_ids = [str(c["course_id"]) for c in courses]
    course_ids_str = ", ".join(course_ids)

    node_schedule_time_column = await _resolve_nodeschedule_time_column()
    node_schedule_at_select = (
        f",\n        ns.{node_schedule_time_column} AS node_schedule_at"
        if node_schedule_time_column
        else ""
    )
    order_by_clause = (
        f"ORDER BY cu.first_name, ns.{node_schedule_time_column} NULLS LAST, ns.id, r.\"order\", n.title"
        if node_schedule_time_column
        else 'ORDER BY cu.first_name, ns.id, r."order", n.title'
    )

    sql = f"""
    SELECT
        ue.user_id AS student_id,
        TRIM(CONCAT(cu.last_name, cu.first_name)) AS student_name,
        n.title AS task_title,
        ns.id AS node_schedule_id,
        r.metric AS rubric_metric,
        r."order" AS rubric_order,
        e.score AS human_score,
        rge.gpt_score,
        rge.gpt_comment AS rubric_feedback,
        ge.overall_comment AS overall_feedback{node_schedule_at_select}
    FROM core_evaluation e
    JOIN core_nodeprogrs np ON e.node_progrs_id = np.id
    JOIN core_nodeschedule ns ON np.node_schedule_id = ns.id
    JOIN core_node n ON ns.node_id = n.id
    JOIN core_nodeversion nv ON ns.node_version_id = nv.id
    JOIN core_coursenodeversionrelation cnvr ON nv.id = cnvr.node_version_id
    JOIN core_userenrolments ue ON np.user_enrolments_id = ue.id
    JOIN core_user cu ON ue.user_id = cu.id
    LEFT JOIN core_gptevaluation ge ON ge.node_progrs_id = np.id
    LEFT JOIN core_rubric r ON e.rubric_id = r.id
    LEFT JOIN core_rubricgptevaluation rge ON rge.evaluation_id = e.id
    WHERE cnvr.course_id IN ({course_ids_str})
    {order_by_clause}
    """
    return await _query_legacy(sql)


async def get_total_rubric_count(user_group_id: int) -> int:
    """Get the total number of rubric-bearing tasks for a course group."""
    sql_courses = f"SELECT course_id FROM user_group_course_mapping WHERE user_group_id = {user_group_id}"
    courses = await _query_legacy(sql_courses)
    if not courses:
        return 0
    course_ids = [str(c["course_id"]) for c in courses]
    course_ids_str = ", ".join(course_ids)

    sql = f"""
    SELECT COUNT(DISTINCT n.id) as count
    FROM core_node n
    JOIN core_nodeschedule ns ON n.id = ns.node_id
    JOIN core_nodeversion nv ON ns.node_version_id = nv.id
    JOIN core_coursenodeversionrelation cnvr ON nv.id = cnvr.node_version_id
    JOIN core_rubric r ON r.node_id = n.id
    WHERE cnvr.course_id IN ({course_ids_str})
    """
    res = await _query_legacy(sql)
    return int(res[0]["count"]) if res else 0


async def list_students_by_course(user_group_id: int) -> List[Dict[str, Any]]:
    """List active students enrolled in a specific course (user_group).
    Excludes dropout students (status=INACTIVE with dropout_at set)."""
    sql = f"""
    SELECT
        cu.id AS user_id,
        cu.first_name AS name,
        ugm.role
    FROM user_group_mapping ugm
    JOIN core_user cu ON ugm.user_id = cu.id
    WHERE ugm.user_group_id = {user_group_id}
      AND ugm.role = 'MEMBER'
      AND ugm.status = 'ACTIVE'
      AND ugm.dropout_at IS NULL
      AND TRIM(COALESCE(cu.first_name, '')) != ''
    ORDER BY cu.first_name
    """
    return await _query_legacy(sql)
