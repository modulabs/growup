# Development Plan v2 - GrowUp Quest Score Management System

## Project Summary

교육 과정(아이펠, 에드캠 등)의 퀘스트 점수를 관리하는 웹 시스템.
기존 Google Spreadsheet 운영의 비효율성을 해소하고, Legacy DB(모두연 LMS) 연동을 통해 데이터 정합성을 확보한다.

**핵심 변경 사항**: Phase 1부터 Legacy DB 연동을 핵심 기능으로 통합 (n8n webhook 방식).

---

## Tech Stack

| 레이어 | 기술 | 비고 |
|-------|------|-------|
| Frontend | SvelteKit + Tailwind CSS | Static Adapter, GitHub Pages 배포 |
| Backend | Python FastAPI + httpx | 서버 배포 |
| GrowUp DB | PostgreSQL | 자체 관리, READ-WRITE |
| Legacy DB | PostgreSQL (READ-ONLY) | n8n webhook HTTP 호출을 통해 접근 |
| 인증 | JWT (이름 + 전화번호 via Legacy) | 간이 인증 |

---

## Phase 1 - 로컬 개발 & 핵심 기능 (2주)

### 1-1. 환경 세팅 (Day 1)
- **Backend**: FastAPI 프로젝트 초기화, requirements.txt (fastapi, uvicorn, sqlalchemy, alembic, httpx, python-jose, pydantic)
- **Backend**: GrowUp DB용 로컬 PostgreSQL 구성 (Docker Compose)
- **Backend**: .env 설정 (DATABASE_URL, N8N_LEGACY_DB_WEBHOOK_URL, JWT_SECRET)
- **Backend**: SQLAlchemy 모델 정의 + Alembic 마이그레이션 세팅
- **Backend**: n8n webhook 클라이언트 모듈 (`legacy_service.py`) 구현
- **Frontend**: SvelteKit 초기화, Tailwind CSS 설치, API 클라이언트 세팅
- **Frontend**: .env 설정 (PUBLIC_API_BASE_URL=http://localhost:8000)

### 1-2. GrowUp DB 스키마 & Legacy 연동 (Day 1-2)
- **GrowUp DB 테이블**: `cached_users`, `cached_courses`, `cached_enrollments`, `quests`, `quest_scores`, `bonus_scores`, `facilitator_favorites`
- **캐시 테이블**: Legacy DB에서 동기화된 데이터를 저장하며 `last_synced_at` 타임스탬프 포함
- **Legacy 서비스 구현**: `verify_user()`, `list_active_courses()`, `list_students_by_course()`, `get_user_role()`
- **캐시 서비스 구현**: `sync_courses()`, `sync_students_for_course()`
- n8n webhook 연결 테스트 및 초기 데이터 동기화 스크립트 작성

### 1-3. 인증 (Day 2)
- `POST /api/v1/auth/login`: 이름 + 전화번호 → n8n webhook → Legacy DB 검증 → JWT 발급
- JWT 미들웨어: `legacy_user_id` 및 `role` 포함
- 역할 기반 접근 제어 (COACH=퍼실리테이터, MEMBER=학생)
- 로그인 검증 로직: Legacy의 `core_user` + `core_userprivacy` + `user_group_mapping` 참조

### 1-4. 학생 기능 (Day 2-3)
- **Backend**:
  - `GET /api/v1/student/scores`: 본인 퀘스트 점수 조회 (GrowUp DB)
  - `GET /api/v1/student/scores/summary`: 과정별 총점 요약
- **Frontend**:
  - 로그인 페이지 (이름 + 전화번호 입력)
  - 학생 대시보드 (Legacy 캐시 기반 수강 과정 목록)
  - 점수 조회 페이지 (ScoreTable, ScoreSummary 컴포넌트)

### 1-5. 퍼실리테이터 - 과정 및 퀘스트 관리 (Day 3-5)
- **Backend**:
  - `GET /api/v1/courses`: Legacy 캐시 기반 과정 목록 (즐겨찾기 포함)
  - `GET /api/v1/courses/{id}/quests`: 퀘스트 목록 (GrowUp DB)
  - `POST /api/v1/courses/{id}/quests`: 퀘스트 생성
  - `PUT /api/v1/quests/{id}`: 퀘스트 수정
  - `DELETE /api/v1/quests/{id}`: 퀘스트 삭제
  - `GET /api/v1/courses/{id}/students`: 과정별 학생 목록 (Legacy 캐시)
- **Frontend**:
  - 퍼실 대시보드 (과정 목록, ★ 즐겨찾기 기능)
  - 과정 상세 페이지 (퀘스트 목록)
  - 퀘스트 생성/수정 모달

### 1-6. 퍼실리테이터 - 채점 (Day 5-7)
- **Backend**:
  - `GET /api/v1/quests/{id}/students`: 학생 목록 + 기존 점수 현황
  - `POST /api/v1/quests/{id}/scores`: 점수 일괄 입력 (Batch Save)
  - `PUT /api/v1/scores/{id}`: 개별 점수 수정
- **Frontend**:
  - 채점 테이블 (GradingTable 컴포넌트)
  - `quest_type`별 점수 입력 UI:
    - sub: Pass/Non-pass
    - main: 0-5
    - datathon: 0-10
    - ideathon: 0-20
  - 제출/미제출 체크박스 (0점과 미제출 구분)

### 1-7. 통합 테스트 & 데모 (Day 7)
- 전체 플로우 테스트: 로그인 → 과정 선택 → 퀘스트 생성 → 채점 → 학생 조회
- Legacy 데이터 동기화 검증 및 버그 수정

---

## Phase 2 - 서버 배포 & 확장 기능 (2주)

### 2-1. 서버 배포 (Day 1-2)
- **Backend**: 서버 환경 구축 (Python, systemd/Docker), 원격 PostgreSQL 설정
- **Backend**: FastAPI 배포 (uvicorn + nginx), HTTPS (Let's Encrypt) 적용
- **Backend**: GitHub Pages용 CORS 설정, 프로덕션 n8n webhook URL 설정
- **Frontend**: SvelteKit 정적 빌드 및 GitHub Pages 배포, GitHub Actions CI/CD 구축

**인프라 구조**:
```
[GitHub Pages]              [Server]                    [Legacy DB]
 SvelteKit Static  ──API──▶  FastAPI  ──n8n webhook──▶  모두연 LMS PostgreSQL
                              │                          (READ-ONLY)
                              ▼
                         [GrowUp DB]
                          PostgreSQL
                          (READ-WRITE)
```

### 2-2. 비정규 점수 (Day 2-3)
- **Backend**: 비정규 점수(Bonus Scores) CRUD API 구현
- **Frontend**: BonusScoreModal 구현, 학생 점수 조회 화면 통합

### 2-3. 퀘스트 복사 및 즐겨찾기 (Day 3-4)
- **Backend**: 이전 기수 퀘스트 복사 로직, 과정 즐겨찾기 토글 API
- **Frontend**: QuestCopyModal 구현, 과정 목록 즐겨찾기 ★ UI 적용

### 2-4. 데이터 내보내기 (Day 4)
- **Backend**: CSV/JSON 데이터 내보내기 엔드포인트 구현
- **Frontend**: ExportButton 컴포넌트 추가

### 2-5. 안정화 (Day 5-7)
- 기존 스프레드시트 데이터 마이그레이션
- 퍼실리테이터 대상 사용성 테스트 및 피드백 반영
- 모바일 반응형 최적화 및 에러 모니터링 설정

---

## Phase 3 (향후) - ODN 통합
- ODN 어드민 내 점수 관리 기능 완전 통합
- 성장 지표 대시보드 (날짜 기반 성장 추이 시각화)
- Legacy DB의 노드 점수 연동
- 데이터 자동 동기화 스케줄링 (Cron job)

---

## 로컬 개발 환경 Quick Start

### Backend
```bash
cd growup/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# .env 설정 (N8N_LEGACY_DB_WEBHOOK_URL 포함 필수)
cp .env.example .env

alembic upgrade head
python scripts/initial_sync.py  # Legacy 데이터 초기 동기화
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd growup/frontend
npm install
echo "PUBLIC_API_BASE_URL=http://localhost:8000" > .env
npm run dev
```

### Docker Compose (GrowUp DB 전용)
```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: growup
      POSTGRES_USER: growup
      POSTGRES_PASSWORD: growup_dev
    ports:
      - "5432:5432"
```

---

## 팀 역할 분담

| 담당자 | 역할 |
|--------|------|
| 조해창 | 프론트엔드 + 백엔드 개발 |
| 박형철 | 코드 리뷰, 퍼실리테이터 관점 피드백 |
| 차정은 | 지표 정의, 요구사항 관리, 사용성 검증 |

---

## 우선순위 정리

```
[필수 - Phase 1]
  로그인 (이름+전화번호 via Legacy)
  Legacy DB 연동 (n8n webhook, 과정/학생 동기화)
  퍼실: 과정 목록 (Legacy 데이터 기반)
  퍼실: 퀘스트 CRUD
  퍼실: 채점 (4종류 점수 체계, 0점 vs 미제출 구분)
  학생: 본인 점수 조회

[중요 - Phase 2]
  비정규 점수 관리
  이전 기수 퀘스트 복사
  과정 즐겨찾기
  점수 내보내기 (CSV)
  서버 배포 + GitHub Pages 배포

[향후 - Phase 3]
  ODN 어드민 통합
  성장 지표 대시보드
  노드 점수 연동
  자동 동기화 스케줄링
```
