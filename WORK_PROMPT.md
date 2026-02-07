# GrowUp Phase 1 — Ralph Loop 작업 프롬프트

## 지시

아래 4개 문서를 먼저 읽고, End State가 달성될 때까지 코드를 구현하라.

### 참조 문서
1. `/Users/admin/Documents/growup/docs/PRD-backend.md`
2. `/Users/admin/Documents/growup/docs/PRD-frontend.md`
3. `/Users/admin/Documents/growup/docs/DEVELOPMENT-PLAN.md`
4. `/Users/admin/MODULABS_AIFFEL_SCORE/documents/03_Legacy_Data_Query.md`

### 현재 상태
- Git repo: `SunCreation/MODULABS_AIFFEL_SCORE` (private, branch: main)
- PRD 문서 3개 + .gitignore 커밋 완료
- `backend/`, `frontend/` 디렉토리 구조만 존재, **코드 파일 0개**

---

## End State (모두 충족해야 완료)

### 1. Backend 동작
- `docker compose up -d` → 로컬 PostgreSQL(growup DB) 실행
- `cd backend && pip install -r requirements.txt && alembic upgrade head && uvicorn app.main:app --reload --port 8000` → FastAPI 서버 정상 기동
- `GET /health` → 200 OK
- `POST /api/v1/auth/login` (name + phone) → n8n webhook 경유 Legacy DB 검증 → JWT 반환
- `GET /api/v1/student/courses`, `GET /api/v1/student/courses/{id}/scores` → 학생 점수 조회
- `GET /api/v1/facilitator/courses` → 과정 목록
- `POST /api/v1/facilitator/courses/{id}/quests` → 퀘스트 생성
- `POST /api/v1/facilitator/quests/{id}/scores` → 점수 일괄 저장
- 점수 비즈니스 규칙 적용: sub(0/1), main(0-5), datathon(0-10, 0.5단위), ideathon(0-20, 0.5단위), 미제출 시 score=null

### 2. Frontend 동작
- `cd frontend && npm install && npm run dev` → SvelteKit 개발 서버 기동
- 로그인 페이지: 이름 + 전화번호 → JWT 저장 → 역할별 라우팅 (학생→/student, 퍼실→/facilitator)
- 학생: 수강 과정 목록 → 과정 선택 → 퀘스트 점수 테이블
- 퍼실: 과정 목록 → 과정 선택 → 퀘스트 CRUD 모달 → 채점 테이블 (4종류 점수, 0점 vs 미제출 구분, 일괄 저장)

### 3. 검증 체크리스트
- [ ] `docker compose up -d` 성공
- [ ] `alembic upgrade head` 에러 없음
- [ ] `uvicorn app.main:app` 기동 후 `/health` 200 반환
- [ ] Backend Python 파일 전체 구문 오류 없음
- [ ] Frontend `npm run build` 에러 없음

---

## 핵심 제약

- **Legacy DB**: 런타임 접근은 `httpx`로 n8n webhook HTTP POST만. 직접 DB 연결 금지.
  - n8n webhook: POST `{query: "SQL"}` → JSON 배열 응답
  - URL은 환경변수 `N8N_LEGACY_DB_WEBHOOK_URL`
  - 개발 중 쿼리 테스트: `mcp_n8n-postgres_execute_sql` 도구 사용
- **GrowUp DB**: Docker PostgreSQL (docker-compose.yml). Async SQLAlchemy + asyncpg.
- **Legacy 참조 ID**: bigint (`legacy_*_id`), UUID 아님
- **시크릿**: .env에만 저장. 코드/커밋에 절대 포함 금지.
- **Frontend**: SvelteKit + Tailwind CSS. 절대 React/Next.js 아님.
- **Phase 1 범위만**: 비정규 점수 UI, 퀘스트 복사, 데이터 내보내기, 즐겨찾기는 Phase 2 (지금 안 함)
  - 단, Backend API에는 bonus-scores, favorite 엔드포인트 포함해도 됨 (DB 스키마에 있으므로)
