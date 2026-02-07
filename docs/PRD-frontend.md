# Frontend PRD - GrowUp Quest Score Management UI (v2)

## 1. Overview

GrowUp 프론트엔드는 퀘스트 점수 관리 시스템의 웹 UI다.
v2에서는 기존 GrowUp DB와 모두연 Legacy DB를 함께 사용하는 **Dual-DB 아키텍처**를 반영한다.
사용자 인증 및 과정/학생 정보는 Legacy DB(n8n 연동)를 통해 가져오며, 퀘스트 및 점수 데이터는 GrowUp DB에서 관리한다.

- **Tech Stack**: SvelteKit (Static Adapter)
- **배포**: GitHub Pages (정적 사이트)
- **스타일**: Tailwind CSS
- **API 통신**: Fetch API (백엔드 REST API 호출)
- **데이터 소스**:
  - Legacy DB: 사용자 인증, 과정 목록, 학생 명단 (백엔드/n8n 경유)
  - GrowUp DB: 퀘스트 설정, 점수 데이터, 비정규 점수

---

## 2. 사용자 흐름

### 2.1 공통 - 로그인
- **인증 방식**: 이름 + 전화번호 입력.
- **백엔드 로직**: 백엔드가 n8n 웹훅을 통해 Legacy DB(`core_user`, `core_userprivacy`)에서 사용자 확인.
- **회원가입**: 별도 가입 절차 없음. Legacy 시스템에 등록된 사용자만 접근 가능.
- **역할 결정**: `user_group_mapping.role` 필드에 따라 결정.
  - `COACH` → 퍼실리테이터 (모든 과정 조회 및 채점 권한)
  - `MEMBER` → 학생 (본인 점수만 조회 권한)

### 2.2 데이터 로딩 및 캐싱 UX
- **지연 시간 대응**: Legacy 데이터 조회 시 50-200ms 추가 지연 발생 가능.
- **로딩 UI**: 데이터 페칭 중 Skeleton Screen 또는 Spinner 표시.
- **브라우저 캐싱**:
  - 과정 목록: `localStorage`에 캐싱.
  - 학생 명단: `sessionStorage`에 캐싱.
- **새로고침**: 과정/학생 목록 화면에 "새로고침" 버튼을 배치하여 백엔드 캐시 강제 동기화 트리거.

### 2.3 학생 - 점수 조회
- **과정 선택**: Legacy DB의 수강 등록 데이터에 기반하여 본인이 참여 중인 과정만 표시.
- **점수 확인**: GrowUp DB에 저장된 퀘스트 점수 및 비정규 점수 조회.

### 2.4 퍼실리테이터 - 과정 및 학생 관리
- **과정 목록**: Legacy DB의 모든 활성 과정(`user_group.name`) 표시. 즐겨찾기(★) 설정된 과정 우선 정렬.
- **학생 명단**: 채점 화면 진입 시 해당 과정의 학생 명단을 Legacy DB에서 동기화하여 표시.
- **명단 관리**: 프론트엔드에서 수동 학생 추가/삭제 기능 없음 (Legacy 데이터 연동).

---

## 3. 페이지 구조 (SvelteKit Routes)

```
src/routes/
  +page.svelte                     # 리다이렉트 → /login
  +layout.svelte                   # 공통 레이아웃

  login/
    +page.svelte                   # 로그인 (이름+전화번호)

  student/
    +page.svelte                   # 학생 대시보드 (수강 과정 선택)
    [courseId]/
      +page.svelte                 # 과정별 점수 조회

  facilitator/
    +page.svelte                   # 퍼실 대시보드 (전체 과정 목록)
    courses/
      [courseId]/
        +page.svelte               # 과정 상세 (퀘스트 목록)
    quests/
      [questId]/
        +page.svelte               # 채점 화면 (학생 명단 포함)
    scoring/
      +page.svelte                 # (선택) 점수 종합 뷰
```

---

## 4. 주요 컴포넌트

### 4.1 공통
- `LoginForm.svelte`: 이름 + 전화번호 입력 폼.
- `Navbar.svelte`: 로그아웃, 역할 표시, 홈 이동.
- `Toast.svelte`: 성공/에러 알림.
- `LoadingSkeleton.svelte`: (v2 추가) Legacy 데이터 로딩용 스켈레톤 UI.
- `RefreshButton.svelte`: (v2 추가) 캐시 동기화 트리거 버튼.

### 4.2 학생용
- `ScoreTable.svelte`: 퀘스트 점수 테이블 (읽기 전용).
- `ScoreSummary.svelte`: 총점 요약 카드.
- `BonusScoreList.svelte`: 비정규 점수 내역 (읽기 전용).

### 4.3 퍼실용
- `CourseCard.svelte`: 과정 카드 (기수명 표시, 즐겨찾기 ★ 포함).
- `QuestCard.svelte`: 퀘스트 카드 (채점 진행률 표시).
- `QuestCreateModal.svelte`: 퀘스트 생성 모달.
- `QuestCopyModal.svelte`: 이전 기수 퀘스트 복사 모달.
- `GradingTable.svelte`: 학생별 점수 입력 테이블.
- `ScoreInput.svelte`: quest_type별(sub/main/data/idea) 입력 UI.
- `BonusScoreModal.svelte`: 비정규 점수 추가 모달.
- `ExportButton.svelte`: CSV/JSON 내보내기.

---

## 5. 상태 관리 및 캐싱

### 5.1 Svelte Stores
- `auth.ts`: JWT 토큰, `legacy_user_id`, 역할 정보.
- `courses.ts`: 과정 목록, 즐겨찾기 상태.
- `quests.ts`: 퀘스트 목록.
- `scores.ts`: 채점 데이터.
- `cache.ts`: (v2 추가) `last_synced_at`, `is_cached` 상태 관리.

### 5.2 캐싱 전략
- API 응답에 `is_cached: boolean` 포함 시, UI에 "캐시된 데이터임"을 암시하는 디자인 적용.
- Legacy DB 장애 시: `localStorage`의 마지막 성공 데이터를 보여주며 "최근 동기화: {timestamp}" 경고 배너 표시.

---

## 6. API 통신 레이어

- **백엔드 중심**: 모든 Legacy DB 통신은 백엔드가 담당. 프론트는 백엔드 API만 호출.
- **에러 핸들링**:
  - Legacy 사용자 미존재: "등록되지 않은 사용자입니다. 모두연 LMS 등록 여부를 확인해주세요." 메시지 출력.
  - Legacy DB 타임아웃: 캐시 데이터 표시 및 경고 알림.

---

## 7. 타입 정의 (v2 업데이트)

```typescript
// src/lib/types/

interface User {
  legacy_user_id: number; // BigInt 대응
  name: string;           // core_user.first_name
  phone: string;          // core_userprivacy.phone_number
  role: 'student' | 'facilitator';
}

interface Course {
  legacy_course_id: number;
  legacy_user_group_name: string; // e.g., "AI 리서처 16기"
  is_active: boolean;
  is_favorite: boolean;
}

interface Quest {
  id: string;             // GrowUp DB UUID
  legacy_course_id: number;
  quest_number: number;
  quest_type: 'sub' | 'main' | 'datathon' | 'ideathon';
  title?: string;
  quest_date: string;
  graded_count: number;
  total_students: number;
}

interface QuestScore {
  id: string;             // GrowUp DB UUID
  quest_id: string;
  legacy_student_id: number;
  student_name: string;   // core_user.first_name
  score: number | null;
  is_submitted: boolean;
}

interface BonusScore {
  id: string;
  legacy_student_id: number;
  student_name: string;
  score: number;
  reason: string;
  given_by_name: string;
  given_at: string;
}
```

---

## 8. UI/UX 요구사항

### 8.1 로딩 및 에러 처리 (v2 강조)
- **Skeleton Screen**: 과정 목록과 학생 명단 로딩 시 필수 적용.
- **경고 배너**: Legacy DB 연결 실패 시 상단에 노란색 경고 배너 ("오프라인 모드: {timestamp} 데이터") 표시.

### 8.2 채점 UX (v1 유지)
- Tab 키 이동, 범위 유효성 검사, 변경 항목만 저장.
- 0.5 단위 입력 지원 (Datathon/Ideathon).
- 미제출 체크 해제 시 점수 입력 필드 활성화.

### 8.3 접근성
- 충분한 색상 대비, 키보드 네비게이션 지원.

---

## 9. 배포 구성

- **GitHub Pages (Static)**: `adapter-static` 설정 및 `base` 경로 설정 유지.
- **환경 변수**: `PUBLIC_API_BASE_URL`을 통해 백엔드 주소 관리.

---

## 10. Phase별 프론트 범위 (v2 업데이트)

| Phase | 범위 |
|-------|------|
| **Phase 1** | 로그인(Legacy 연동), 학생 점수 조회, 퍼실 채점, Legacy 기반 과정/학생 목록 (핵심 기능 전체) |
| **Phase 2** | 비정규 점수, 퀘스트 복사, 데이터 내보내기, 즐겨찾기, 모바일 최적화, 서버 배포 |
