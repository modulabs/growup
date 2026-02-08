# MCP 개선 요청사항 및 Google Drive 검색 불가 원인 분석

> 작성일: 2026-02-08
> 작성자: GrowUp 프로젝트 개발 중 발견된 이슈 정리

---

## 1. 핵심 문제: Google Sheets MCP `search_spreadsheets`가 공유 드라이브 파일을 검색하지 못함

### 1-1. 증상

| 검색 방법 | "교육통합관리" 검색 결과 |
|---|---|
| **Google Drive 웹 UI** (hc.cho@modulabs.co.kr 로그인) | PDA5기, PDA4기, PDA3기, DS8기, DS7기, DS6기, 온15기, 온16기 등 **8건 이상** |
| **MCP `search_spreadsheets`** (동일 계정 OAuth 토큰) | PDA5기, DS7기, 온15기, 온16기, 통합관리(교운/취업) **5건만** |

- 웹 UI에서 보이는 PDA4기, PDA3기, PDA2기, PDA1기, DS8기, DS6기, DS4기 시트가 API 검색에서 **완전히 누락**
- 그러나 해당 시트의 ID를 알면 `get_sheet_data`(Sheets API)로 **정상 읽기 가능**

### 1-2. 근본 원인 (확정)

**Google Drive API `files.list`의 기본 검색 범위(`corpora`) 파라미터 누락**

Google Drive API `files.list`는 기본값으로 `corpora=user`를 사용한다.
이는 **인증된 사용자의 "내 드라이브"에 있거나, 사용자에게 명시적으로 공유된 파일만** 검색한다.

```
# 현재 MCP가 호출하는 방식 (추정)
GET https://www.googleapis.com/drive/v3/files
  ?q=name contains '교육통합관리' and mimeType='application/vnd.google-apps.spreadsheet'
  # corpora 파라미터 없음 → 기본값 "user" 적용
  # supportsAllDrives 없음
  # includeItemsFromAllDrives 없음
```

반면 **Google Drive 웹 UI**는 내부적으로 `corpora=allDrives` + 조직 전체 인덱스를 사용하여:
- 모든 공유 드라이브
- 조직 내 "링크가 있는 사용자" 설정의 파일
- 사용자에게 명시적 공유 안 됐지만 조직 내 검색 가능한(discoverable) 파일

을 모두 검색한다.

### 1-3. 해결 방법

Drive API `files.list` 호출 시 아래 3개 파라미터를 **반드시** 추가해야 한다:

```python
# 수정된 API 호출
service.files().list(
    q="name contains '교육통합관리' and mimeType='application/vnd.google-apps.spreadsheet'",
    corpora="allDrives",                  # ← 핵심: 모든 드라이브 대상 검색
    includeItemsFromAllDrives=True,       # ← 공유 드라이브 항목 포함
    supportsAllDrives=True,               # ← 공유 드라이브 지원 활성화
    pageSize=100,
    fields="files(id, name, createdTime, modifiedTime, owners, webViewLink, driveId)"
).execute()
```

| 파라미터 | 역할 | 기본값 | 필요한 값 |
|---|---|---|---|
| `corpora` | 검색 대상 범위 | `"user"` (내 드라이브만) | `"allDrives"` (전체) |
| `includeItemsFromAllDrives` | 공유 드라이브 항목 포함 여부 | `False` | `True` |
| `supportsAllDrives` | 공유 드라이브 API 지원 선언 | `False` | `True` |

### 1-4. `corpora` 옵션 비교

| 값 | 검색 범위 | 비고 |
|---|---|---|
| `"user"` (기본) | 내 드라이브 + 나에게 공유된 파일 | **현재 MCP가 사용 중 (추정)** |
| `"drive"` | 특정 공유 드라이브 1개 | `driveId` 파라미터 필수 |
| `"domain"` | 조직(도메인) 전체에서 검색 가능한 파일 | Google Workspace 한정 |
| `"allDrives"` | 내 드라이브 + 모든 공유 드라이브 | **이것을 써야 웹 UI와 동일** |

### 1-5. 왜 `get_sheet_data`는 되는가?

| API | 엔드포인트 | 권한 체크 방식 |
|---|---|---|
| Drive API `files.list` | `GET /drive/v3/files` | **파일 열거(enumerate) 권한** — 명시적 공유 or corpora 범위 내 |
| Sheets API `spreadsheets.values.get` | `GET /v4/spreadsheets/{id}/values/{range}` | **파일 접근(access) 권한** — "링크가 있는 조직 내 사용자" 설정이면 ID만으로 접근 가능 |

즉, **검색 불가 ≠ 읽기 불가**. 두 API의 권한 모델이 다르다.

---

## 2. Google Sheets MCP 개선 요청사항

### 2-1. `search_spreadsheets`에 공유 드라이브 검색 지원 추가

**현재**: `search_spreadsheets(query, max_results)` — 내 드라이브만 검색
**요청**: 내부 `files.list` 호출에 `corpora="allDrives"`, `includeItemsFromAllDrives=True`, `supportsAllDrives=True` 추가

```diff
# MCP 서버 소스 코드 수정 (추정 위치)
  results = service.files().list(
      q=f"name contains '{query}' and mimeType='application/vnd.google-apps.spreadsheet'",
+     corpora="allDrives",
+     includeItemsFromAllDrives=True,
+     supportsAllDrives=True,
      pageSize=max_results,
      fields="files(id, name, createdTime, modifiedTime, owners, webViewLink)"
  ).execute()
```

### 2-2. `search_spreadsheets`에 `driveId` 파라미터 추가

**현재**: 특정 공유 드라이브 지정 검색 불가
**요청**: `search_spreadsheets(query, max_results, drive_id?)` 형태로 확장

```python
# drive_id가 주어지면 corpora="drive"로 특정 드라이브만 검색
if drive_id:
    params["corpora"] = "drive"
    params["driveId"] = drive_id
else:
    params["corpora"] = "allDrives"
```

### 2-3. `list_spreadsheets`에 공유 드라이브 지원

**현재**: `list_spreadsheets(folder_id)` — 공유 드라이브 폴더 지정 시 결과 불완전
**요청**: `supportsAllDrives=True`, `includeItemsFromAllDrives=True` 파라미터 추가

### 2-4. `list_folders`에 공유 드라이브 지원

**현재**: 공유 드라이브 내 폴더 탐색 시 일부 누락 가능
**요청**: 동일하게 `supportsAllDrives`, `includeItemsFromAllDrives` 추가

---

## 3. Google Docs MCP 개선 요청사항

### 3-1. `listGoogleSheets(driveId=...)` — Permission Denied 오류

**현재**: `google-docs` MCP와 `google-docs-lecture` MCP 모두 `listGoogleSheets(driveId="0AMSelRj_7lnLUk9PVA")` 호출 시 Permission denied 오류 발생

**추정 원인**: Drive API 호출 시 `supportsAllDrives=True` 파라미터 누락, 또는 `corpora="drive"` 대신 기본값 사용

**요청**: 공유 드라이브 ID 지정 시 올바른 API 파라미터 전달

---

## 4. 우리 프로젝트의 현재 워크어라운드

위 MCP 제한사항으로 인해, GrowUp 프로젝트에서는 다음과 같이 우회하고 있다:

1. **API 검색 가능한 시트** (5건): 직접 `search_spreadsheets`로 찾아서 import
2. **API 검색 불가능한 시트**: 사용자에게 Google Drive 웹 UI에서 URL을 직접 공유받아, spreadsheet ID를 추출한 후 `get_sheet_data`로 읽기
3. **GrowUp 앱 UI**: 퍼실이 시트 ID를 직접 입력하여 import하는 방식 — 검색 기능에 의존하지 않음

### 검색 가능한 "교육통합관리" 시트 (API 접근 가능)

| # | 시트명 | ID | 상태 |
|---|---|---|---|
| 1 | AI/DATA 캠프_PDA5기 교육 통합 관리 | `1jCso2KY1OkL7YouKPNpaUXNiK9Kpxdy-YGeEbZZOuf4` | ✅ |
| 2 | 아이펠 캠퍼스_온16기_리서처_교육통합관리 | `14sGkbzQnvrwFEkTAK-GTpx4KbWxmq8d6g5Y2vJs35uw` | ✅ |
| 3 | Al/DATA캠프_DS7기 교육 통합 관리 | `1abDR3kSIqwZcxHe90QN_rTAQqUbLL0BGHvPyNp02e4k` | ✅ |
| 4 | 아이펠 캠퍼스_온15기_리서치_교육통합관리 | `1BKPnRPbmzoufvg7P0aqDN0nErMnQfKMq1spElKzFsDM` | ✅ |
| 5 | 아이펠 캠퍼스_교육 운영 통합 관리(교육운영, 취업) | `1WMRhCcunGOe3v9j3YFWHiz9rQDQdG01bkZ5_o3Je-o4` | 퀘스트탭 없음 |

### 검색 불가능한 시트 (사용자 URL 공유 필요)

- PDA4기, PDA3기, PDA2기, PDA1기
- DS8기, DS6기, DS4기
- 기타 이전 기수 교육통합관리 시트

---

## 5. 참고: 공유 드라이브 목록

```
모두의연구소  — ID: 0AF1eizSdmDsSUk9PVA
사내_자동화TF — ID: 0AI-6VFgrpkTPUk9PVA
커뮤니티팀    — ID: 0AA3MfxHzAqLlUk9PVA
KDT교육      — ID: 0AMSelRj_7lnLUk9PVA
```

---

## 6. 참고: OAuth 토큰 정보

- **계정**: `hc.cho@modulabs.co.kr`
- **토큰 타입**: `authorized_user`
- **Scopes**: `https://www.googleapis.com/auth/spreadsheets`, `https://www.googleapis.com/auth/drive`
- **scope는 충분** — `drive` scope는 `files.list`에 필요한 모든 권한 포함. 문제는 scope가 아니라 API 호출 시 `corpora` 파라미터 누락.
