# GrowUp 퀘스트 임포트 현황

> 최종 업데이트: 2026-02-09

## 임포트 완료 과정 (9개)

| course_id | 과정명 | 시트 ID | 퀘스트 | 점수 | 학생 매칭 | 비고 |
|---|---|---|---|---|---|---|
| 2 | 아이펠 리서치 15기 | `1BKPnRPbmzoufvg7P0aqDN0nErMnQfKMq1spElKzFsDM` | 36 | 648 | 18명 | Layout A |
| 3 | 데이터 사이언티스트 5기 | `1G-w3d1grs-PHsOb7zhxgKiigOSxL1Tey4XD4BAap20g` | 12 | 168 | 14명 | Layout B |
| 4 | 데이터 분석가 4기 | `19uVyaOJiO0Gyl3r6Z954md2Bs4HEbuyC7BnRbTsDTs4` | 11 | 154 | 14명 | 1 unmatched: "우등생(기준)" |
| 10 | 데이터 사이언티스트 6기 | `1BpVUJ_UTqqE6PI4nu4iN_VQPaeF8sPIH1-DJ9PzhGmI` | 22 | 396 | 18명 | Layout B |
| 11 | 데이터 사이언티스트 7기 | `1abDR3kSIqwZcxHe90QN_rTAQqUbLL0BGHvPyNp02e4k` | 22 | 132 | 6명 | Layout B |
| 12 | 데이터 사이언티스트 8기 | `1quWGSAcpaxR-0GHYfJSTMq3gIN4zLv2-rYxfMb6FtCc` | 22 | 198 | 9명 | Layout B |
| 13 | AI 엔지니어 1기 | `129SyAU7YCTZpzpT0D7zGuWMN2e0cADFCuoFPlA_Uj60` | 38 | 684 | 18명 | Layout A |
| 14 | 데이터 분석가 5기 | `1jCso2KY1OkL7YouKPNpaUXNiK9Kpxdy-YGeEbZZOuf4` | 11 | 341 | 31명 | Layout B |
| 15 | AI 리서처 16기 | `14sGkbzQnvrwFEkTAK-GTpx4KbWxmq8d6g5Y2vJs35uw` | 35 | 665 | 19명 | Layout A |

**합계**: 퀘스트 209개, 점수 3,386건

## 미임포트 과정

### 통합관리 시트 미발견

| course_id | 과정명 | DB 학생 수 | 사유 |
|---|---|---|---|
| 1 | 아이펠 리서치 14기 | 26명 | Google Drive 전체 검색에서 "14기 통합관리" 시트 미발견. 시트가 존재하지 않거나 권한 없음 |
| 16 | AI 리서처 8기 | 0명 | 학생 0명 — 실제 운영 과정인지 확인 필요 |
| 17 | 바이브코딩 5기 | 4명 | 통합관리 시트 없음 |

### Legacy DB에 과정 미등록 (PDA 1~3기)

| 시트명 | 시트 ID | 사유 |
|---|---|---|
| PDA3기 교육 통합 관리 | `1bfLPBjKfYATcHg7QQX829ve-QbgsHDNJVB8eFTaIayY` | Legacy DB에 과정 없음 |
| PDA2기 교육 통합 관리 | `1JLUGL54rtJ1lCdIaLle1w8dB1L_iVOuSotvRKw7DMh8` | Legacy DB에 과정 없음 |
| PDA1기 교육 통합 관리 | `1zck897sKVBA2p8szpy4XHGyWjsdYCx7N-ZmxaFzz7nM` | Legacy DB에 과정 없음 |

### 퀘스트 시트 없음 (통합관리 시트 존재하나 "퀘스트" 탭 없음)

| 시트명 | 시트 ID | 사유 |
|---|---|---|
| 재직자 기획_개발 4기 | `1KeSaZ1yErRWRfUgHQD8iIkw97ggelh28c74USVbvpas` | 퀘스트 탭 미존재 |
| 재직자 LLM 4기 | `1cUKDhE0Qyx6QFf6ClTrYIt9oMVJJNPLidzAoqCnZISk` | 미사용 |
| 재직자 기획_개발 3기 | `1kdtDu77MNRxcP039tihXiI9xp6eRTeTI1Kc-85tghYM` | 미사용 |
| 재직자 데이터분석 4기(사본) | `1iAlr88PK_RYn_C-vCHsmC6iPz1nRZ2ihviLu6CDWQGA` | 미사용(사본) |

## 레이아웃 유형 설명

- **Layout A**: Col A = "고유번호", 날짜 행 존재, 퀘스트 데이터 Col G(7)부터 시작
- **Layout B**: Col A = "학번", 날짜 행 없음, 퀘스트 데이터 Col E(5)부터 시작

## 사용자 확인 필요 사항

1. **아이펠 리서치 14기** (course_id=1): 통합관리 시트가 다른 이름으로 존재하는지, 또는 해당 기수에는 시트가 만들어지지 않았는지 확인 필요
2. **PDA 1~3기**: Legacy DB에 과정이 없어 자동 임포트 불가. 수동으로 과정/학생을 GrowUp DB에 등록 후 임포트할지, 또는 무시할지 결정 필요
3. **AI 리서처 8기** (course_id=16): 학생 0명 — 실제 운영 예정 과정인지, 오류 데이터인지 확인
4. **바이브코딩 5기** (course_id=17): 학생 4명이지만 통합관리 시트 없음 — 퀘스트 관리 대상인지 확인
