# FMEA Reference Index

변압기 FMEA 스킬의 참조 문서 목록입니다.

---

## 핵심 참조 문서

### FMEA 방법론
| 파일 | 용도 | 주요 내용 |
|------|------|----------|
| [aiag-vda-7step.md](aiag-vda-7step.md) | AIAG-VDA 7단계 프로세스 | 7단계 상세, FCM 분석, DFMEA/PFMEA |
| [fmea-concepts.md](fmea-concepts.md) | FMEA 기본 개념 | 정의, 목적, 핵심 용어 |
| [5why-vs-fmea.md](5why-vs-fmea.md) | FMEA vs 5 Why 차이 | 기능→고장 순서, 영향→형태→원인 금지 |
| [diamond-structure.md](diamond-structure.md) | 다이아몬드 구조 | 1:N:M:K 확장, 원인/형태 비율 ≥2.0 |

### 고장 분석
| 파일 | 용도 | 주요 내용 |
|------|------|----------|
| [failure-mode-diversity.md](failure-mode-diversity.md) | 고장형태 다양화 | 부품별 고장형태 목록, 구체적 현상 |
| [failure-mode-forbidden.md](failure-mode-forbidden.md) | E열 금지어 | 소음, 진동, ~증가, ~저하 금지 |
| [failure-effect-phases.md](failure-effect-phases.md) | 고장영향 3시점 | 부품/시스템/최종사용자 영향 |
| [function-analysis.md](function-analysis.md) | 기능 분석 | 부품별 필수 기능 정의 |

### Excel 생성
| 파일 | 용도 | 주요 내용 |
|------|------|----------|
| [excel-generation.md](excel-generation.md) | Excel 생성 가이드 | 20컬럼 구조, 셀 병합, 양식 |
| [excel-format-guide.md](excel-format-guide.md) | Excel 양식 상세 | Row 높이, 색상, 테두리 |
| [column-details.md](column-details.md) | 컬럼별 상세 | A-T 컬럼 정의, 입력 규칙 |
| [cell-comments.md](cell-comments.md) | 셀 입력 안내 | 20개 메시지, 셀별 안내 |
| **[ghj-format-rules.md](ghj-format-rules.md)** | **G/H/J열 형식 규칙** | **화살표 체인, 멀티라인, 기준값** |
| **[cef-format-rules.md](cef-format-rules.md)** | **C/E/F열 상세 형식** | **태그, 상세설명, 판단근거** |

### 평가 기준
| 파일 | 용도 | 주요 내용 |
|------|------|----------|
| [sod-criteria.md](sod-criteria.md) | S/O/D 평가 기준 | 변압기 특화 1-10점 기준 |
| [lifecycle-balance.md](lifecycle-balance.md) | 라이프사이클 균형 | 설계/재료/제작/시험 4단계 |

### 품질 검증
| 파일 | 용도 | 주요 내용 |
|------|------|----------|
| [quality-checklist.md](quality-checklist.md) | 품질 체크리스트 | 검증 항목, 통과 기준 |
| [quality-examples.md](quality-examples.md) | 품질 예시 | Good/Bad 예시 |
| [validation-guidelines.md](validation-guidelines.md) | 검증 가이드라인 | 6개 검증 함수 사용법 |
| [critical-improvements.md](critical-improvements.md) | 핵심 개선 사항 | 체계적 준비, 품질 원칙 |
| **[anti-hallucination.md](anti-hallucination.md)** | **[!!] 날조 방지** | **Read-Before-Write, 출처 검증, 날조 방지** |

---

## 도메인 참조 문서

### 변압기 도메인
| 파일 | 용도 | 주요 내용 |
|------|------|----------|
| [iljin-background.md](iljin-background.md) | 일진전기 배경 | 회사 정보, 제품 범위 |
| [manufacturing-process.md](manufacturing-process.md) | 제작 공정 | 변압기 제작 단계 |
| [organization.md](organization.md) | 조직 구조 | 팀별 역할, FMEA 담당 |
| [terminology.md](terminology.md) | 용어 사전 | 변압기/FMEA 용어 |

### WebSearch 연동
| 파일 | 용도 | 주요 내용 |
|------|------|----------|
| [websearch-mandatory.md](websearch-mandatory.md) | WebSearch 필수 | 5개 출처, 검색 전략 |
| [websearch-mapping.md](websearch-mapping.md) | 검색 매핑 | 부품별 검색 키워드 |

### 워크플로우
| 파일 | 용도 | 주요 내용 |
|------|------|----------|
| [workflow.md](workflow.md) | 워크플로우 상세 | STEP 1-4 상세 절차 |
| [example-core.md](example-core.md) | 예시: 철심 | 철심 FMEA 예시 |

### 내부 문서 활용 (PRIMARY!)
| 파일 | 용도 | 주요 내용 |
|------|------|----------|
| [internal-docs-index.md](internal-docs-index.md) | 내부 문서 목록 | CHECK SHEET, W/R/I/P시리즈, TD시리즈 |
| [internal-docs-summary.md](internal-docs-summary.md) | 내부 문서 요약 | 핵심 내용 요약 |
| [qa-data-mapping.md](qa-data-mapping.md) | **QA 자료 -> FMEA 매핑** | CHECK SHEET, W/R/I/P시리즈, TD시리즈 활용법 |
| [glossary.md](glossary.md) | 용어 사전 | 전문용어+쉬운표현 병기 규칙 |

---

## 아카이브

| 파일 | 상태 | 이유 |
|------|------|------|
| [archived/critical-workflow.md](archived/critical-workflow.md) | DEPRECATED | critical-improvements.md로 통합 |

---

## 빠른 참조

### STEP별 참조
- **STEP 0 (기능분석+QA DB)**: function-analysis.md, qa-data-mapping.md, internal-docs-index.md
- **STEP 1 (내부문서+WebSearch)**: **qa-data-mapping.md (PRIMARY!)**, websearch-mandatory.md (보완용)
- **STEP 2 (페르소나)**: function-analysis.md, failure-mode-diversity.md
- **STEP 3 (FMEA 생성)**: diamond-structure.md, failure-effect-phases.md, lifecycle-balance.md
- **STEP 4 (Excel)**: excel-generation.md, column-details.md, cell-comments.md

> **[!] 우선순위**: 내부 문서 (CHECK SHEET, W/R/I/P시리즈, TD시리즈) -> WebSearch (보완용)

### 검증 스크립트 관련
- **validate_failure_mode.py**: failure-mode-forbidden.md
- **validate_lifecycle_coverage.py**: lifecycle-balance.md, failure-effect-phases.md
- **validate_function_failure_mapping.py**: diamond-structure.md, function-analysis.md
- **generate_fmea_excel.py**: excel-generation.md, column-details.md, cell-comments.md
