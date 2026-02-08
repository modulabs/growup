"""Google Sheets → Quest & Score import service.

Reads a quest sheet from a course-specific spreadsheet and upserts
Quest + QuestScore rows into the GrowUp DB.

Supports two sheet layouts:

Layout A (DS7기, 리서치15기):
  Row 0 header: [고유번호, 이름, 길드, 과정, 세부과정, 훈련상태, 퀘스트명, Sub Quest 01, ...]
  Row 1 dates:  [..., ..., ..., ..., ..., ..., 시행일자, 2025-11-17, ...]
  Row 2+:       student data rows
  Quest cols start at G (index 7), Col G is a label column ("퀘스트명")

Layout B (온라인4기, 퀘스트&출결):
  Row 0 header: [학번, 이름, 길드, 과정, 상태, QUEST_01, QUEST_02, ...]
  Row 1+:       student data rows (no date row)
  Quest cols start at F (index 5)

Student matching: Uses **name** (Col B for both layouts) to look up
legacy_user_id from cached_users + cached_enrollments. The sheet's Col A
(고유번호/학번) is NOT the Legacy DB user_id.
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
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
from app.models.bonus import BonusScore
from app.models.cache import CachedEnrollment, CachedUser
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


# ── Layout detection ──


@dataclass
class SheetLayout:
    name_col: int = 1  # Column index for student name
    quest_start_col: int = 7  # First quest column index
    has_date_row: bool = True  # Whether row 1 has dates
    student_start_row: int = 2  # First student data row index
    layout_type: str = "A"  # "A" or "B"


def _detect_layout(rows: list[list[str]]) -> SheetLayout:
    """Auto-detect the sheet layout from the header row."""
    if not rows:
        return SheetLayout()

    header = rows[0]
    first_cell = (header[0].strip() if header else "").lower()

    # Layout B: starts with "학번"
    if first_cell == "학번":
        return SheetLayout(
            name_col=1,
            quest_start_col=5,
            has_date_row=False,
            student_start_row=1,
            layout_type="B",
        )

    # Layout A: check for "퀘스트명" or "퀘스트" label in col F/G area
    if len(header) > 6:
        col6 = header[6].strip() if len(header) > 6 else ""
        if col6 in ("퀘스트명", "퀘스트"):
            return SheetLayout(
                name_col=1,
                quest_start_col=7,
                has_date_row=True,
                student_start_row=2,
                layout_type="A",
            )

    # Default: assume Layout A
    return SheetLayout()


# ── Parsing helpers ──

# Layout A patterns
_QUEST_SUB_NAMED_RE = re.compile(r"Sub\s+Quest\s*(\d+)", re.IGNORECASE)
_QUEST_SUB_TAG_RE = re.compile(r"QUEST[_\s]*(\d+)\s*\(([A-C])\)", re.IGNORECASE)
_QUEST_MAIN_RE = re.compile(r"Main\s+QUEST[_\s]*(\d+)", re.IGNORECASE)
_QUEST_DATATHON_RE = re.compile(r"(?:데이터톤|datathon|DATAthon|DLthon)", re.IGNORECASE)
_QUEST_IDEATHON_RE = re.compile(r"(?:아이디어톤|ideathon)", re.IGNORECASE)

# Layout B pattern: bare QUEST_XX (no tag, no "Main" prefix)
_QUEST_BARE_RE = re.compile(r"^QUEST[_\s]*(\d+)$", re.IGNORECASE)

# Non-quest columns to skip
_SKIP_COLS = {
    "비정규점수총계",
    "디스코드",
    # "디스코드 소통왕",
    # "아낌없이 주는 그루",
    # "쉐밸그투",
    # "퍼실재량점수",
    "TOTAL",
    "신호등",
    "총점",
    "퀘스트 점수",
    # "비정규점수",  # Allowed for bonus import
    "퀘스트 보상",
    "출결",
    "퀘스트 점수\n 부여 기록",
}

_BONUS_COLS_PREFIXES = {
    "비정규",
    "디스코드 소통왕",
    "아낌없이 주는 그루",
    "쉐밸그투",
    "퍼실재량점수",
}


@dataclass
class ParsedQuest:
    col_index: int
    quest_type: str  # sub | main | datathon | ideathon
    quest_number: int
    title: str
    quest_date: Optional[date] = None


@dataclass
class ParsedBonusColumn:
    col_index: int
    reason: str


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
    students_matched: int = 0
    students_unmatched: int = 0
    errors: list[str] = field(default_factory=list)


def _parse_quest_header(
    name: str, col_idx: int
) -> Optional[ParsedQuest | ParsedBonusColumn]:
    """Parse a quest column header into type + number, or detect bonus column."""
    name = name.strip()
    if not name:
        return None

    # Skip known non-quest columns
    if name in _SKIP_COLS or name.replace("\n", "") in _SKIP_COLS:
        return None

    # Bonus Score check
    if "비정규" in name and "총계" not in name:
        return ParsedBonusColumn(col_index=col_idx, reason=name)

    for prefix in _BONUS_COLS_PREFIXES:
        if name.startswith(prefix):
            return ParsedBonusColumn(col_index=col_idx, reason=name)

    # Main quest: "Main QUEST_XX" — check first to avoid sub-match
    m = _QUEST_MAIN_RE.search(name)
    if m:
        return ParsedQuest(
            col_index=col_idx,
            quest_type="main",
            quest_number=int(m.group(1)),
            title=name,
        )

    # Sub quest named: "Sub Quest 01" (DS7기 format)
    m = _QUEST_SUB_NAMED_RE.search(name)
    if m:
        return ParsedQuest(
            col_index=col_idx,
            quest_type="sub",
            quest_number=int(m.group(1)),
            title=name,
        )

    # Sub quest tagged: "QUEST_XX (A/B/C)" (리서치15기 format)
    m = _QUEST_SUB_TAG_RE.search(name)
    if m:
        return ParsedQuest(
            col_index=col_idx,
            quest_type="sub",
            quest_number=int(m.group(1)),
            title=name,
        )

    # Datathon
    if _QUEST_DATATHON_RE.search(name):
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

    # Bare QUEST_XX (Layout B format, no tag) → sub
    m = _QUEST_BARE_RE.match(name)
    if m:
        return ParsedQuest(
            col_index=col_idx,
            quest_type="sub",
            quest_number=int(m.group(1)),
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
    if val is None:
        return None, False

    val = str(val).strip()
    if not val or val == "미제출" or val.lower() == "null":
        return None, False

    if val == "0점/미제출":
        return None, False

    # Skip N/A markers
    if val.upper() in ("#N/A", "N/A", "#REF!", "#VALUE!", "#DIV/0!"):
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


def _col_idx_to_a1(idx: int) -> str:
    """Convert 0-based column index to A1 notation (0->A, 26->AA)."""
    res = ""
    while idx >= 0:
        res = chr(ord("A") + (idx % 26)) + res
        idx = (idx // 26) - 1
    return res


def _fetch_bonus_notes(
    spreadsheet_id: str, sheet_name: str, start_col: int, end_col: int
) -> dict[tuple[int, int], str]:
    """Fetch cell notes for a specific column range.

    Returns:
        dict: {(row_idx, col_idx): note_content}
    """
    svc = _get_sheets_service()
    col_a = _col_idx_to_a1(start_col)
    col_b = _col_idx_to_a1(end_col)
    range_str = f"{sheet_name}!{col_a}:{col_b}"

    try:
        resp = (
            svc.spreadsheets()
            .get(
                spreadsheetId=spreadsheet_id,
                ranges=[range_str],
                includeGridData=True,
                fields="sheets(data(startRow,startColumn,rowData(values(note))))",
            )
            .execute()
        )
    except Exception as e:
        logger.error(f"Failed to fetch notes for range {range_str}: {e}")
        return {}

    notes = {}
    sheets = resp.get("sheets", [])
    if not sheets:
        return {}

    for sheet in sheets:
        data_list = sheet.get("data", [])
        for grid_data in data_list:
            start_row = grid_data.get("startRow", 0)
            start_col_grid = grid_data.get("startColumn", 0)
            row_data = grid_data.get("rowData", [])

            for r_offset, row in enumerate(row_data):
                row_idx = start_row + r_offset
                values = row.get("values", [])
                for c_offset, cell in enumerate(values):
                    col_idx = start_col_grid + c_offset
                    note = cell.get("note", "").strip()
                    if note:
                        notes[(row_idx, col_idx)] = note
    return notes


def _parse_giver_from_note(note: str) -> Optional[str]:
    """Extract giver name from note format 'Date/Reason/Score/Giver'.

    Example: "0724/아낌없이주는그루/+2/조웅제" -> "조웅제"
    Handles multiline notes by picking the first valid giver found or joining unique givers.
    """
    if not note:
        return None

    givers = set()
    for line in note.split("\n"):
        parts = line.split("/")
        if len(parts) >= 4:
            giver = parts[-1].strip()
            if giver:
                givers.add(giver)

    if not givers:
        return None

    return ", ".join(sorted(givers))


def _parse_date_from_note(note: str) -> Optional[datetime]:
    """Extract date from note format 'Date/Reason/Score/Giver'.

    Example: "0724/..." -> 2025-07-24
    """
    if not note:
        return None

    # Use first line's date
    line = note.split("\n")[0]
    parts = line.split("/")
    if len(parts) >= 1:
        date_part = parts[0].strip()
        if len(date_part) == 4 and date_part.isdigit():
            try:
                # Assume 2025 for now (Research 14th was 2025)
                # Ideally, infer from course start date
                year = 2025
                month = int(date_part[:2])
                day = int(date_part[2:])
                return datetime(year, month, day, tzinfo=timezone.utc)
            except ValueError:
                pass
    return None


# ── Name-based student matching ──


async def _build_name_to_ids(db: AsyncSession, course_id: int) -> dict[str, list[int]]:
    """Build a mapping from student name → list of legacy_user_ids
    for students enrolled in the given course.

    Uses cached_users + cached_enrollments.
    """
    stmt = (
        select(CachedUser.legacy_user_id, CachedUser.name)
        .join(
            CachedEnrollment,
            CachedEnrollment.legacy_user_id == CachedUser.legacy_user_id,
        )
        .where(CachedEnrollment.legacy_course_id == course_id)
    )
    rows = (await db.execute(stmt)).all()

    name_map: dict[str, list[int]] = defaultdict(list)
    for user_id, name in rows:
        clean_name = name.strip()
        if clean_name:
            name_map[clean_name].append(user_id)

    return dict(name_map)


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

    if not rows:
        result.errors.append("시트가 비어있습니다.")
        return result

    # 2. Detect layout
    layout = _detect_layout(rows)
    logger.info(
        f"Sheet layout detected: type={layout.layout_type}, "
        f"quest_start={layout.quest_start_col}, "
        f"has_date_row={layout.has_date_row}, "
        f"student_start={layout.student_start_row}"
    )

    min_rows = layout.student_start_row + 1
    if len(rows) < min_rows:
        result.errors.append(f"시트에 데이터가 부족합니다 (최소 {min_rows}행 필요).")
        return result

    row_headers = rows[0]

    # 3. Parse quest columns
    parsed_quests: list[ParsedQuest] = []
    parsed_bonuses: list[ParsedBonusColumn] = []

    for col_idx in range(layout.quest_start_col, len(row_headers)):
        obj = _parse_quest_header(row_headers[col_idx], col_idx)
        if obj is None:
            continue

        if isinstance(obj, ParsedQuest):
            # Attach date from row 1 (Layout A only)
            if layout.has_date_row and len(rows) > 1:
                row_dates = rows[1]
                if col_idx < len(row_dates):
                    obj.quest_date = _parse_date(row_dates[col_idx])

            if obj.quest_date is None:
                obj.quest_date = date.today()

            parsed_quests.append(obj)
        elif isinstance(obj, ParsedBonusColumn):
            parsed_bonuses.append(obj)

    if not parsed_quests and not parsed_bonuses:
        result.errors.append("퀘스트 또는 비정규 점수 컬럼을 찾을 수 없습니다.")
        return result

    logger.info(
        f"Parsed {len(parsed_quests)} quest columns and {len(parsed_bonuses)} bonus columns"
    )

    # Fetch notes for bonus columns
    notes_map: dict[tuple[int, int], str] = {}
    if parsed_bonuses:
        min_col = min(pb.col_index for pb in parsed_bonuses)
        max_col = max(pb.col_index for pb in parsed_bonuses)
        logger.info(f"Fetching notes for columns {min_col} to {max_col}")
        notes_map = _fetch_bonus_notes(spreadsheet_id, sheet_name, min_col, max_col)

    # 4. Build name → legacy_user_id mapping
    name_to_ids = await _build_name_to_ids(db, course_id)
    if not name_to_ids:
        result.errors.append(
            "이 과정에 등록된 학생이 없습니다. 먼저 학생 동기화를 실행하세요."
        )
        return result

    logger.info(f"Name mapping built: {len(name_to_ids)} enrolled students")

    # 5. Upsert quests
    quest_map: dict[int, Quest] = {}  # col_index → Quest object
    now = datetime.now(timezone.utc)

    for pq in parsed_quests:
        stmt = select(Quest).where(
            Quest.cached_course_id == course_id,
            Quest.quest_type == pq.quest_type,
            Quest.quest_number == pq.quest_number,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()

        if existing:
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

    # 6. Parse student rows
    matched_students = set()
    unmatched_names = set()

    for row_idx in range(layout.student_start_row, len(rows)):
        row = rows[row_idx]
        if len(row) <= layout.name_col:
            continue

        # Get student name
        student_name = row[layout.name_col].strip() if row[layout.name_col] else ""
        if not student_name:
            continue

        # Look up legacy_user_id by name
        ids = name_to_ids.get(student_name)
        if not ids:
            unmatched_names.add(student_name)
            continue

        # Use first matched ID (if multiple, log warning)
        student_id = ids[0]
        if len(ids) > 1:
            logger.warning(
                f"Student name '{student_name}' matches multiple IDs: {ids}. "
                f"Using first: {student_id}"
            )

        matched_students.add(student_name)

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

            if existing_score:
                existing_score.score = score if score is not None else None
                existing_score.is_submitted = is_submitted
                existing_score.graded_by_legacy_user_id = facilitator_id
                existing_score.graded_at = now
                result.scores_updated += 1
            else:
                new_score = QuestScore(
                    quest_id=quest.id,
                    legacy_student_id=student_id,
                    score=score if score is not None else None,
                    is_submitted=is_submitted,
                    graded_by_legacy_user_id=facilitator_id,
                    graded_at=now,
                )
                db.add(new_score)
                result.scores_created += 1

        # Parse Bonus Scores
        for pb in parsed_bonuses:
            cell_val = ""
            if pb.col_index < len(row):
                cell_val = row[pb.col_index]

            score, _ = _parse_score_cell(cell_val, "main")

            # Extract note for giver
            note_content = notes_map.get((row_idx, pb.col_index), "")
            giver_name = _parse_giver_from_note(note_content)
            parsed_date = _parse_date_from_note(note_content)
            bonus_date = parsed_date if parsed_date else now

            if score is not None and score > 0:
                stmt = select(BonusScore).where(
                    BonusScore.cached_course_id == course_id,
                    BonusScore.legacy_student_id == student_id,
                    BonusScore.reason == pb.reason,
                )
                existing_bonus = (await db.execute(stmt)).scalar_one_or_none()

                if existing_bonus:
                    if (
                        existing_bonus.score != score
                        or existing_bonus.given_by_name != giver_name
                        or existing_bonus.given_at != bonus_date
                    ):
                        existing_bonus.score = score
                        existing_bonus.given_by_name = giver_name
                        existing_bonus.given_at = bonus_date
                        result.scores_updated += 1
                else:
                    new_bonus = BonusScore(
                        cached_course_id=course_id,
                        legacy_student_id=student_id,
                        score=score,
                        reason=pb.reason,
                        given_by_legacy_user_id=facilitator_id,
                        given_by_name=giver_name,
                        given_at=bonus_date,
                    )
                    db.add(new_bonus)
                    result.scores_created += 1

    result.students_matched = len(matched_students)
    result.students_unmatched = len(unmatched_names)

    if unmatched_names:
        sample = sorted(unmatched_names)[:10]
        logger.warning(f"Unmatched students ({len(unmatched_names)}): {sample}")
        if len(unmatched_names) <= 10:
            result.errors.append(
                f"매칭 실패 학생 {len(unmatched_names)}명: {', '.join(sample)}"
            )
        else:
            result.errors.append(
                f"매칭 실패 학생 {len(unmatched_names)}명 (일부: {', '.join(sample)}...)"
            )

    await db.commit()

    logger.info(
        f"Import complete: quests={result.quests_created}c/{result.quests_updated}u, "
        f"scores={result.scores_created}c/{result.scores_updated}u, "
        f"students matched={result.students_matched}, unmatched={result.students_unmatched}"
    )

    return result
