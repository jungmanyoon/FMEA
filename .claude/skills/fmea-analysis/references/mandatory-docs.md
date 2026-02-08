# mandatory-docs.md - 부품별 필수 문서 시스템

## 개요

FMEA 작성 시 **누락 방지**를 위한 부품별 필수 참조 문서 체크리스트 시스템.

**핵심 원칙**: 검색이 아닌 **강제 체크리스트**로 사용

---

## 파일 위치

| 파일 | 경로 | 용도 |
|------|------|------|
| `mandatory_docs_by_component.json` | `02.참고자료/_fmea_index/` | 부품별 필수 문서 목록 (v4.0) |
| `_converted/` | `02.참고자료/_converted/` | 변환된 텍스트 파일 (MD/JSON) |

---

## JSON 구조 (v4.0)

```json
{
  "_meta": {
    "version": "4.0",
    "description": "계층 상속 + 텍스트 검색 기반 부품-문서 매핑",
    "statistics": {
      "total_parts": 164,
      "total_mappings": 3490,
      "empty_design": 0,
      "empty_manufacturing": 0,
      "empty_testing": 0,
      "match_sources": {
        "category_inherit": 328,
        "category_series_inherit": 1510,
        "part_match": 1652
      }
    }
  },

  "categories": {
    "중신": {
      "철심": {
        "규소강판": {
          "functions": ["자속의 경로를 제공한다", "변압비를 결정한다"],
          "function_keywords": ["규소강판", "자속", "변압비"],
          "mandatory_docs": {
            "design": [
              {
                "file": "_converted/02.CHECK_SHEET/중신 CHECK SHEET_24_R02_xlsm.json",
                "doctype": "CHECK",
                "lifecycle": "design",
                "priority": "high",
                "source": "category_inherit"
              }
            ],
            "manufacturing": [
              {
                "file": "_converted/생산_작업요령/IEQT-T-W018_초고압 변압기 철심조립 작업요령_Rev.04_pdf.md",
                "doctype": "W",
                "lifecycle": "manufacturing",
                "priority": "high",
                "source": "category_series_inherit"
              }
            ],
            "testing": [
              {
                "file": "_converted/QA_시험요령/IEQT-T-P005_무부하손 및 여자전류 시험요령_pdf.md",
                "doctype": "P",
                "lifecycle": "testing",
                "priority": "high",
                "source": "category_series_inherit"
              }
            ]
          }
        }
      }
    }
  }
}
```

### v4.0 계층 구조

```
categories
  -> {카테고리} (중신/권선/단자/외함/외장)
    -> {도면명} (철심, 권선자재표, 단자 자재표, ...)
      -> {부품명} (규소강판, CLAMP, 압착단자, ...)
        -> functions: [기능 목록]
        -> function_keywords: [검색 키워드]
        -> mandatory_docs:
           -> design: [{file, doctype, lifecycle, priority, source}]
           -> manufacturing: [{file, doctype, lifecycle, priority, source}]
           -> testing: [{file, doctype, lifecycle, priority, source}]
```

### 문서 매핑 소스 (source 필드)

| source | 설명 | 매핑 수 |
|--------|------|---------|
| `category_inherit` | 카테고리 CHECK/WORKFLOW 상속 | 328 |
| `category_series_inherit` | 카테고리 W/I/P 시리즈 상속 | 1,510 |
| `part_match` | 부품명/기능 키워드 텍스트 매칭 | 1,652 |
| **합계** | | **3,490** |

### 파일 경로 형식

모든 `file` 경로는 `_converted/` 하위의 텍스트 파일:

| 원본 형식 | 변환 형식 | 경로 예시 |
|----------|----------|----------|
| .xlsx/.xlsm | .json | `_converted/02.CHECK_SHEET/중신 CHECK SHEET_24_R02_xlsm.json` |
| .pdf | .md | `_converted/97.도시바TD/TD4/IJTD_4143_REV0.0_pdf.md` |
| .docx | .md | `_converted/생산_작업요령/IEQT-T-W018_..._docx.md` |

**[!] 중요**: 파일 경로는 `02.참고자료/` 기준 상대경로. Read 시 절대경로로 변환:
```
C:\Users\jmyoo\Desktop\FMEA\02.참고자료\{file경로}
```

---

## 사용 방법

### 1. FMEA 작성 전 (Pre-FMEA)

```
1. Read: 02.참고자료/_fmea_index/mandatory_docs_by_component.json
2. categories.{카테고리}.{도면명}.{부품명}.mandatory_docs 확인
3. design/manufacturing/testing 각 배열의 file 경로로 실제 파일 Read
```

**Read 순서 (라이프사이클별)**:

| 단계 | 문서 유형 | 변환 형식 | H/J열 즉시 작성 |
|------|----------|----------|---------------|
| 1-A | design: CHECK, WORKFLOW | .json (Excel) | 설계 단계 |
| 1-B | manufacturing: W, I, C | .md (PDF/Word) | 제작 단계 |
| 1-C | testing: P, I | .md (PDF) | 시험 단계 |
| 1-D | testing/design: R, TD | .md (PDF) | 재료/설계 단계 |

### 2. FMEA 작성 후 (Post-FMEA)

라이프사이클 균형 검증:

```
[LIFECYCLE BALANCE]
  [O] 설계: 25.0% (5개)
  [O] 재료: 20.0% (4개)
  [O] 제작: 35.0% (7개)
  [!] 시험: 10.0% (2개)  <- 15% 미만, 추가 필요!
```

---

## FMEA 컬럼별 필수 문서 매핑

| FMEA 컬럼 | 참조 문서 유형 | 용도 |
|-----------|---------------|------|
| B. 기능 | CHECK, WORKFLOW, TD | 기능 정의 출처 |
| C. 고장형태 | TD, C, W | 고장형태 출처 |
| F. 고장원인(설계) | CHECK, WORKFLOW, C | 설계 단계 원인 |
| G. 고장원인(재료) | R, C | 재료 단계 원인 (수입검사) |
| H. 고장원인(제작) | W, I | 제작 단계 원인 (작업표준, 공정검사) |
| I. 고장원인(시험) | P, I | 시험 단계 원인 (시험요령) |
| K. 예방조치 | W, C, CHECK | 예방 방법 출처 |
| L. 검출조치 | I, P, R | 검출 방법 출처 |

---

## 라이프사이클 4단계 균형

| 단계 | 문서 유형 | 목표 비율 |
|------|----------|----------|
| **설계** | CHECK, WORKFLOW, C | 15-25% |
| **재료** | R, C | 20-30% |
| **제작** | W, I | 25-35% |
| **시험** | P, I | 15-25% |

**경고**: 특정 단계 50% 초과 시 과다 집중으로 판정

---

## GATE 체크포인트 통합

### GATE 0 (Pre-FMEA)

| 체크 항목 | 방법 |
|----------|------|
| mandatory_docs JSON Read 완료 | `mandatory_docs_by_component.json` 에서 부품 조회 |
| design 문서 Read 완료 | `mandatory_docs.design[]` 파일 모두 Read |
| manufacturing 문서 Read 완료 | `mandatory_docs.manufacturing[]` 파일 모두 Read |
| testing 문서 Read 완료 | `mandatory_docs.testing[]` 파일 모두 Read |
| 공통 문서 Read 완료 | 다이어그램, 용어집, SOD기준표 |

### GATE 1-3 (기존)

기존 GATE에 추가 검증:

```text
GATE 1/2/3 체크포인트:
  ...
  [NEW] 문서 출처 검증:
    - 기능: [출처 문서명]
    - 고장형태: [출처 문서명]
    - 고장원인(설계): [출처 문서명]
    - 고장원인(재료): [출처 문서명]
    - 고장원인(제작): [출처 문서명]
    - 고장원인(시험): [출처 문서명]
```

### GATE 4 (Post-FMEA) - 역검증

| 체크 항목 | 방법 |
|----------|------|
| 라이프사이클 균형 | F열 태그 비율 확인 (설계/재료/제작/시험) |
| 출처 누락 검출 | 모든 항목에 출처 명시 여부 |
| 문서 커버리지 | mandatory_docs 대비 실제 Read한 파일 비율 확인 |

---

## 문서 유형별 파일 패턴 (변환 후)

| 유형 | 변환 파일 패턴 | 예시 |
|------|--------------|------|
| W | `_converted/생산_작업요령/IEQT-T-W###_*_pdf.md` | IEQT-T-W001_클램프도장_..._pdf.md |
| R | `_converted/검사_수입/IEQT-T-R###_*_pdf.md` | IEQT-T-R012_부싱수입검사_..._pdf.md |
| I | `_converted/검사_공정/IEQT-T-I###_*_pdf.md` | IEQT-T-I013_제관품가조립검사_..._pdf.md |
| P | `_converted/QA_시험요령/IEQT-T-P###_*_pdf.md` | IEQT-T-P014_절연역률시험_..._pdf.md |
| C | `_converted/생산_기술일반/IEQT-T-C###_*_pdf.md` | IEQT-T-C022_부싱조립지침_..._pdf.md |
| TD | `_converted/97.도시바TD/TD#/IJTD_####_*_pdf.md` | IJTD_4143_REV0.0_pdf.md |
| CHECK | `_converted/02.CHECK_SHEET/*_xlsm.json` | 중신 CHECK SHEET_24_R02_xlsm.json |
| WORKFLOW | `_converted/03.Work_Flow_Sheet/*_xlsx.json` | 중신설계 Work Flow Sheet_..._xlsx.json |

---

## 카테고리별 공통 문서

### 카테고리 -> CHECK/WORKFLOW (design 상속)

| 카테고리 | CHECK SHEET | WORKFLOW |
|----------|-------------|----------|
| 중신 | 중신 CHECK SHEET_24_R02 | 중신설계 Work Flow Sheet |
| 권선 | 권선 CHECK SHEET_24_R06 | 권선설계 Work Flow Sheet |
| 단자 | 단자 CHECK SHEET_25_R09 | 전기설계 Work Flow Sheet |
| 외함 | 외함 CHECK SHEET_24_R03 | 외함외장설계 Work Flow Sheet |
| 외장 | 외장 CHECK SHEET_24_R07 | 외함외장설계 Work Flow Sheet |

### 카테고리 -> W/I/P 시리즈 (manufacturing/testing 상속)

| 카테고리 | manufacturing (W/I) | testing (P) |
|----------|-------------------|-------------|
| 중신 | W010,W018,W022,W026,I011 | P001,P005,P007,P010,P012 |
| 권선 | W007,W008,W009,W025,I005,I007 | P001,P004,P015,P016,P021 |
| 단자 | W027,W028,W030,I007 | P001,P010,P014,P015 |
| 외함 | W002,W003,W024,W031,I013,C018 | P001,P012,P013 |
| 외장 | W011,W012,W013,W023,I007,I015 | P001,P006,P019 |

---

## 부품명 -> 필수 문서 빠른 조회

| 부품 | 핵심 문서 |
|------|----------|
| 규소강판/철심 | W018(철심조립), IJTD_4143(철심설계), P005(무부하손) |
| 클램프 | W001(도장), IJTD_4396(클램프설계) |
| 타이플레이트 | W002(용접), I013(제관품검사), C018(용접WPS) |
| 디스크권선 | W006(원판코일), P016(SFRA), P021(LVI) |
| 부싱 | R012(수입검사), C022(조립지침), P014(Tan Delta) |
| BCT | W027(조립), R014(수입검사) |
| 탱크 | W002(용접), I013(검사), C018~C021(NDT) |
| OLTC | W012(조작장치), R011(수입검사), P019(시험) |

---

## 주의사항

1. **검색이 아닌 체크리스트**: 문서를 찾는 것이 아니라 반드시 읽어야 할 목록
2. **변환 파일 Read**: 원본 바이너리 파일이 아닌 `_converted/` 하위 텍스트 파일 Read
3. **priority 확인**: priority가 "high"인 문서 우선 Read
4. **역검증 필수**: FMEA 완료 후 라이프사이클 균형 검증
5. **3단계 폴백**: 부품 직접 매칭 -> 도면 매칭 -> 카테고리 상속으로 빈 배열 0건
6. **표지/placeholder 배제**: DRM PDF 변환 시 표지만 추출된 파일(100B 이하)은 내용 없음
   - rebuild_index_v4.py에서 표지 전용 파일 자동 필터링 (v4.0)
   - 인덱스는 정상 변환 파일만 참조 (표지 파일 경로 0건)
   - Worker(fmea-worker-collector)가 Read한 파일이 내용 없으면 건너뛰고 동일 문서의 다른 변환본 탐색
