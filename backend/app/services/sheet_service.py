"""Google Sheets → Quest & Score import service.

Reads a '퀘스트' sheet from a course-specific spreadsheet and upserts
Quest + QuestScore rows into the GrowUp DB.

Sheet layout (columns A~F = student info, G~ = quests):
  Row 1 (G~): quest name — "QUEST_XX (B/C)" → sub, "Main QUEST_XX" → main
  Row 2 (G~): quest date  — YYYY-MM-DD
  Row 3+:     student rows
    Col A: legacy user id (고유번호)
    Col B: student name
    G~:    score values — "P"=1, "F"=0, "미제출"=unsubmitted,
           numeric=score, "0점/미제출"=unsubmitted
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.cache import CachedEnrollment
from app.models.quest import Quest, QuestScore

logger = logging.getLogger(__name__)

# ── Google Sheets API helpers ──

_sheets_service = None


def _get_sheets_service():
    global _sheets_service
    if _sheets_service is not None:
        return _sheets_service

    creds_path = settings.GOOGLE_CREDENTIALS_PATH
    if not creds_path:
        raise RuntimeError("GOOGLE_CREDENTIALS_PATH not configured")

    creds = Credentials.from_authorized_user_file(creds_path)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    _sheets_service = build("sheets", "v4", credentials=creds)
    return _sheets_service


def read_sheet(spreadsheet_id: str, sheet_name: str = "퀘스트") -> list[list[str]]:
    """Return all cell values from the given sheet as a 2D list of strings."""
    svc = _get_sheets_service()
    result = (
        svc.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=sheet_name)
        .execute()
    )
    return result.get("values", [])


# ── Parsing helpers ──

_QUEST_SUB_RE = re.compile(r"QUEST[_\s]*(\d+)\s*\(([BC])\)", re.IGNORECASE)
_QUEST_MAIN_RE = re.compile(r"Main\s+QUEST[_\s]*(\d+)", re.IGNORECASE)
_QUEST_DATATHON_RE = re.compile(r"(?:데이터톤|datathon)", re.IGNORECASE)
_QUEST_IDEATHON_RE = re.compile(r"(?:아이디어톤|ideathon)", re.IGNORECASE)


@dataclass
class ParsedQuest:
    col_index: int
    quest_type: str  # sub | main | datathon | ideathon
    quest_number: int
    title: str
    quest_date: Optional[date] = None


@dataclass
class ParsedScore:
    legacy_student_id: int
    student_name: str
    score: Optional[Decimal] = None
    is_submitted: bool = False


@dataclass
class SheetImportResult:
    quests_created: int = 0
    quests_updated: int = 0
    scores_created: int = 0
    scores_updated: int = 0
    errors: list[str] = field(default_factory=list)


def _parse_quest_header(name: str, col_idx: int) -> Optional[ParsedQuest]:
    """Parse a quest column header into type + number."""
    name = name.strip()
    if not name:
        return None

    # Sub quest: QUEST_XX (B) or QUEST_XX (C)
    m = _QUEST_SUB_RE.search(name)
    if m:
        return ParsedQuest(
            col_index=col_idx,
            quest_type="sub",
            quest_number=int(m.group(1)),
            title=name,
        )

    # Main quest: Main QUEST_XX
    m = _QUEST_MAIN_RE.search(name)
    if m:
        return ParsedQuest(
            col_index=col_idx,
            quest_type="main",
            quest_number=int(m.group(1)),
            title=name,
        )

    # Datathon
    if _QUEST_DATATHON_RE.search(name):
        # Try to extract number
        num_match = re.search(r"(\d+)", name)
        num = int(num_match.group(1)) if num_match else 1
        return ParsedQuest(
            col_index=col_idx,
            quest_type="datathon",
            quest_number=num,
            title=name,
        )

    # Ideathon
    if _QUEST_IDEATHON_RE.search(name):
        num_match = re.search(r"(\d+)", name)
        num = int(num_match.group(1)) if num_match else 1
        return ParsedQuest(
            col_index=col_idx,
            quest_type="ideathon",
            quest_number=num,
            title=name,
        )

    return None


def _parse_date(val: str) -> Optional[date]:
    """Try to parse a date string (YYYY-MM-DD or variations)."""
    val = val.strip()
    if not val:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return None


def _parse_score_cell(val: str, quest_type: str) -> tuple[Optional[Decimal], bool]:
    """Parse a single score cell.

    Returns (score, is_submitted).
    """
    val = val.strip()
    if not val or val == "미제출":
        return None, False

    if val == "0점/미제출":
        return None, False

    upper = val.upper()
    if upper == "P":
        return Decimal("1"), True
    if upper == "F":
        return Decimal("0"), True

    # Numeric
    try:
        num = Decimal(val)
        return num, True
    except Exception:
        return None, False


# ── Main import function ──


async def import_from_sheet(
    db: AsyncSession,
    spreadsheet_id: str,
    course_id: int,
    facilitator_id: int,
    sheet_name: str = "퀘스트",
) -> SheetImportResult:
    """Read a Google Sheet and upsert quests + scores for the given course."""
    result = SheetImportResult()

    # 1. Read sheet data
    try:
        rows = read_sheet(spreadsheet_id, sheet_name)
    except Exception as e:
        result.errors.append(f"시트 읽기 실패: {e}")
        return result

    if len(rows) < 2:
        result.errors.append("시트에 데이터가 부족합니다 (최소 2행 필요).")
        return result

    row_headers = rows[0]  # Row 1: quest names
    row_dates = rows[1] if len(rows) > 1 else []  # Row 2: dates

    # 2. Parse quest columns (starting from col G = index 6)
    quest_start_col = 6
    parsed_quests: list[ParsedQuest] = []

    for col_idx in range(quest_start_col, len(row_headers)):
        pq = _parse_quest_header(row_headers[col_idx], col_idx)
        if pq is None:
            continue
        # Attach date from row 2
        if col_idx < len(row_dates):
            pq.quest_date = _parse_date(row_dates[col_idx])
        if pq.quest_date is None:
            pq.quest_date = date.today()
        parsed_quests.append(pq)

    if not parsed_quests:
        result.errors.append(
            "퀘스트 컬럼을 찾을 수 없습니다 (G열부터 QUEST_XX 패턴 필요)."
        )
        return result

    # 3. Get enrolled students for this course (to validate)
    enrolled_result = await db.execute(
        select(CachedEnrollment.legacy_user_id).where(
            CachedEnrollment.legacy_course_id == course_id
        )
    )
    enrolled_ids = {r for r in enrolled_result.scalars().all()}

    # 4. Upsert quests
    quest_map: dict[int, Quest] = {}  # col_index → Quest object
    now = datetime.now(timezone.utc)

    for pq in parsed_quests:
        # Check existing quest by (course_id, quest_type, quest_number)
        stmt = select(Quest).where(
            Quest.cached_course_id == course_id,
            Quest.quest_type == pq.quest_type,
            Quest.quest_number == pq.quest_number,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()

        if existing:
            # Update date and title if changed
            changed = False
            if existing.quest_date != pq.quest_date:
                existing.quest_date = pq.quest_date
                changed = True
            if existing.title != pq.title:
                existing.title = pq.title
                changed = True
            if changed:
                result.quests_updated += 1
            quest_map[pq.col_index] = existing
        else:
            new_quest = Quest(
                cached_course_id=course_id,
                quest_number=pq.quest_number,
                quest_type=pq.quest_type,
                title=pq.title,
                quest_date=pq.quest_date,
                created_by_legacy_user_id=facilitator_id,
            )
            db.add(new_quest)
            await db.flush()
            await db.refresh(new_quest)
            quest_map[pq.col_index] = new_quest
            result.quests_created += 1

    # 5. Parse student rows (row index 2+ = rows[2:])
    for row_idx in range(2, len(rows)):
        row = rows[row_idx]
        if len(row) < 2:
            continue

        # Col A = legacy user id (고유번호)
        raw_id = row[0].strip() if row[0] else ""
        if not raw_id:
            continue
        try:
            student_id = int(raw_id)
        except ValueError:
            # Not a numeric ID, skip
            continue

        # Only process enrolled students
        if student_id not in enrolled_ids:
            continue

        # Parse scores for each quest column
        for pq in parsed_quests:
            quest = quest_map.get(pq.col_index)
            if quest is None:
                continue

            cell_val = ""
            if pq.col_index < len(row):
                cell_val = row[pq.col_index]

            score, is_submitted = _parse_score_cell(cell_val, pq.quest_type)

            # Upsert score
            score_stmt = select(QuestScore).where(
                QuestScore.quest_id == quest.id,
                QuestScore.legacy_student_id == student_id,
            )
            existing_score = (await db.execute(score_stmt)).scalar_one_or_none()

            score_decimal = score if score is not None else None

            if existing_score:
                existing_score.score = score_decimal
                existing_score.is_submitted = is_submitted
                existing_score.graded_by_legacy_user_id = facilitator_id
                existing_score.graded_at = now
                result.scores_updated += 1
            else:
                new_score = QuestScore(
                    quest_id=quest.id,
                    legacy_student_id=student_id,
                    score=score_decimal,
                    is_submitted=is_submitted,
                    graded_by_legacy_user_id=facilitator_id,
                    graded_at=now,
                )
                db.add(new_score)
                result.scores_created += 1

    await db.commit()
    return result
