# Backend PRD v2 - GrowUp Quest Score Management API

## 1. 개요 (Overview)

GrowUp 백엔드는 퀘스트 점수 관리 시스템의 REST API 서버다. v2 아키텍처는 기존 모두연 LMS(Legacy DB)와의 연동을 강화하고, 데이터 무결성과 성능을 위해 **Dual Database (Legacy + GrowUp)** 구조를 채택한다.

- **Tech Stack**: Python (FastAPI) + PostgreSQL + SQLAlchemy + httpx
- **Architecture**: Dual DB (Legacy READ-ONLY + GrowUp READ-WRITE)
- **Legacy Access**: n8n Webhook HTTP 호출 (직접 DB 연결 금지)
- **인증**: 이름 + 전화번호 기반 (Legacy DB 검증) + JWT 토큰 발급

---

## 2. 아키텍처 및 데이터베이스 구성

### 2.1 Dual Database 구조

1. **Legacy DB (READ-ONLY)**: 모두연 LMS PostgreSQL.
   - **접근 방식**: n8n webhook (`N8N_LEGACY_DB_WEBHOOK_URL`)을 통한 HTTP POST 호출.
   - **역할**: 사용자, 과정, 기수, 수강 정보의 원천 데이터(Source of Truth).
2. **GrowUp DB (READ-WRITE)**: 자체 관리 PostgreSQL.
   - **역할**: 퀘스트 정의, 점수, 비정규 점수, 퍼실 즐겨찾기, Legacy 데이터 캐시 저장.

### 2.2 Legacy DB 참조 테이블 (n8n 쿼리 대상)
- `core_user`: id(bigint), first_name(이름), is_coach, is_student
- `core_userprivacy`: user_id, phone_number
- `user_group_mapping`: user_id, user_group_id, role(COACH/MEMBER), enrollment_status
- `user_group`: id, name(기수명), course_semester_id
- `apply_coursesemester`: id, course code(RESEARCH/ELLM), is_active
- `core_course`: id, title
- `core_userenrolments`: user_id, enrol_id, status

### 2.3 GrowUp DB 스키마 (자체 관리)

#### 캐시 테이블 (Legacy 데이터 미러링)
- `cached_users`: legacy_user_id(bigint, PK), name, phone, role, last_synced_at
- `cached_courses`: legacy_course_id(bigint, PK), legacy_user_group_id, name, cohort, category, is_active, last_synced_at
- `cached_enrollments`: legacy_user_id, legacy_course_id (Composite PK)

#### 비즈니스 테이블
- `quests`: id(UUID), cached_course_id(bigint), quest_number, quest_type(enum), title, quest_date, created_by_legacy_user_id(bigint)
- `quest_scores`: id(UUID), quest_id, legacy_student_id(bigint), score(decimal), is_submitted, graded_by_legacy_user_id(bigint)
- `bonus_scores`: id(UUID), cached_course_id(bigint), legacy_student_id(bigint), score, reason, given_by_legacy_user_id(bigint)
- `facilitator_favorites`: id(UUID), legacy_facilitator_id(bigint), cached_course_id(bigint)

---

## 3. 서비스 레이어 아키텍처

- **legacy_service.py**: n8n webhook을 통한 Legacy DB 쿼리 전담.
  - `verify_user(name, phone)`: 이름/번호로 사용자 존재 여부 확인
  - `get_user_role(user_id, course_id)`: 특정 과정에서의 역할 확인
  - `list_active_courses()`: 현재 활성화된 과정 목록 조회
- **cache_service.py**: Legacy 데이터를 GrowUp 캐시 테이블로 동기화.
  - 로그인 시 자동 갱신 및 관리자 수동 갱신 엔드포인트 제공.
- **auth_service.py**: legacy_service로 검증 후 JWT 발급.
- **quest/score/bonus_service.py**: GrowUp DB 기반 비즈니스 로직 처리.

---

## 4. 데이터 흐름 (Data Flow)

### 4.1 로그인 및 인증 흐름
```text
[User] (Name+Phone) 
  -> [Backend] 
    -> [n8n Webhook] (POST {query: "SELECT..."})
      -> [Legacy DB]
    <- [n8n Webhook] (JSON Result)
  -> [Backend] (Verify & Check Role: COACH/MEMBER)
  <- [User] (JWT: legacy_user_id, role, name, active_courses)
```

### 4.2 과정 목록 조회 흐름
```text
[User] (GET /api/v1/courses)
  -> [Backend]
    -> [GrowUp DB] (cached_courses 조회)
    -> (If empty/stale) [legacy_service] -> [n8n] -> [Legacy DB]
    -> [GrowUp DB] (Update Cache)
  <- [User] (Course List)
```

---

## 5. API Endpoints

### 5.1 인증 및 동기화 (Auth & Sync)
- `POST /api/v1/auth/login`: 이름+전화번호 로그인, JWT 반환
- `POST /api/v1/admin/sync/courses`: 전체 과정 동기화 (Legacy -> Cache)
- `POST /api/v1/admin/sync/students/{course_id}`: 특정 과정 학생 동기화
- `GET /api/v1/legacy/courses`: Legacy DB 직접 조회 (검증용)

### 5.2 학생용 (Student)
- `GET /api/v1/student/scores`: 본인의 전체 퀘스트 점수 조회
- `GET /api/v1/student/scores/summary`: 과정별 점수 요약 및 총점

### 5.3 퍼실리테이터용 (Facilitator)
- `GET /api/v1/courses`: 과정 목록 (캐시 기반, 즐겨찾기 우선)
- `POST /api/v1/courses/{id}/favorite`: 즐겨찾기 추가
- `GET /api/v1/courses/{id}/quests`: 과정 내 퀘스트 목록
- `POST /api/v1/quests/{id}/scores`: 점수 일괄 입력/수정 (legacy_student_id 사용)
- `POST /api/v1/courses/{id}/bonus-scores`: 비정규 점수 부여

---

## 6. 비즈니스 규칙 (Business Rules)

1. **데이터 원천**: 학생, 과정, 수강 정보는 무조건 Legacy DB에서 가져오며, GrowUp에서 수동 생성 불가.
2. **캐시 전략**: 로그인 시 사용자 정보 자동 갱신, 관리자 API를 통한 주기적/수동 동기화.
3. **권한 검증**: `user_group_mapping.role`이 `COACH`인 경우 퍼실리테이터, `MEMBER`인 경우 학생 권한 부여.
4. **점수 범위**:
   - `sub`: 0(Non-pass) / 1(Pass)
   - `main`: 0 ~ 5 (정수)
   - `datathon`: 0 ~ 10 (0.5 단위)
   - `ideathon`: 0 ~ 20 (0.5 단위)
5. **참조 무결성**: Legacy DB 엔티티 참조 시 UUID 대신 Legacy의 `bigint` ID를 `legacy_*_id` 필드로 사용.

---

## 7. 기술 세부 사항

- **n8n 연동**: `httpx`를 사용하여 비동기 HTTP POST 호출. 타임아웃 및 재시도 로직 포함.
- **환경 변수**:
  - `DATABASE_URL`: GrowUp DB (PostgreSQL) 접속 정보
  - `N8N_LEGACY_DB_WEBHOOK_URL`: n8n 엔드포인트 URL
  - `JWT_SECRET`: 토큰 서명 키
- **파일 구조**:
  - `app/models/cache.py`: 캐시 테이블 정의
  - `app/services/legacy_service.py`: n8n 통신 로직
  - `app/services/cache_service.py`: 동기화 로직
  - `app/api/v1/admin.py`: 동기화 엔드포인트

---

## 8. Phase별 구성

- **Phase 1 (Local)**: 로컬 PostgreSQL (GrowUp) + n8n Webhook (Legacy).
- **Phase 2 (Server)**: 원격 PostgreSQL (GrowUp) + n8n Webhook (Legacy).
- 모든 단계에서 Legacy DB 직접 연결은 금지되며, 반드시 n8n을 경유함.
