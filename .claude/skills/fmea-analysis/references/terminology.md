# 변압기 핵심 용어 사전 (업무 분야별)

> **[LOCK] 전체 용어집 (SSOT)**: `01.회의/00.회의 자료/01.용어정리/변압기_전문용어집_V2.2.xlsx`
> **용어 정규화 스크립트**: `scripts/load_glossary.py`
> **병기 규칙**: [glossary.md](glossary.md)

**본 파일**: 핵심 용어 80개 요약본 (Quick Reference)

---

## 사용 규칙

| 규칙 | 설명 |
|------|------|
| **"표준 용어" 컬럼 사용** | Excel의 B열 "표준 용어" 값 사용 |
| **"현재 사용" 컬럼 금지** | 별칭/현재사용 대신 표준 용어 |
| **자동 정규화** | `load_glossary.py`의 `normalize_term()` 활용 |

---

**일진전기 초고압 변압기 실무 필수 용어 80개**


## 전기설계팀 (10개)

| 표준 용어 | 한글 용어 | 영문 용어 | 현재 사용 | 출처 |
|----------|----------|----------|----------|------|
| DFMEA | 설계 FMEA | Design Failure Mode and Effects Analysis | 디자인 FMEA | AIAG-VDA |
| CTC | 연속 트랜스포즈 도체 | Continuously Transposed Conductor | CTC 권선 | 변압기 업계 |
| Buchholz | 부흐홀츠 계전기 | Buchholz Relay | 가스 계전기 | IEC 60076 |
| OTI | 유온 지시계 | Oil Temperature Indicator | - | IEC 60076 |
| WTI | 권선 온도 지시계 | Winding Temperature Indicator | - | IEC 60076 |
| HST | 열점 온도 | Hot Spot Temperature | 최고 온도 | IEC 60076-2 |
| LI | 뇌 임펄스 | Lightning Impulse | BIL (Basic Impulse Level) | IEC 60076-3 |
| SI | 개폐 임펄스 | Switching Impulse | SIL | IEC 60076-3 |
| 고압권선 | - | High-voltage winding | HV winding | 내부자료 |
| 저압권선 | - | Low-voltage winding | LV winding | 내부자료 |

## QA팀 (10개)

| 표준 용어 | 한글 용어 | 영문 용어 | 현재 사용 | 출처 |
|----------|----------|----------|----------|------|
| FAT | 공장 인수 시험 | Factory Acceptance Test | 형식 시험 | IEC 60076 |
| SAT | 현장 인수 시험 | Site Acceptance Test | 현장 시험 | IEC 60076 |
| BDV | 절연 파괴 전압 | Breakdown Voltage | 파괴 전압 | IEC 60296 |
| DGA | 용존 가스 분석 | Dissolved Gas Analysis | 가스 분석 | IEC 60599 |
| FRA | 주파수 응답 분석 | Frequency Response Analysis | SFRA | IEC 60076-18 |
| TTR | 권수비 시험 | Turns Ratio Test | 변압비 시험 | IEC 60076 |
| CTQ | 품질 핵심 요소 | Critical to Quality | 핵심 품질 특성 | Six Sigma |
| IPQC | 공정 중 품질 관리 | In-Process Quality Control | 공정 검사 | 일진전기 내부 |
| IR | 절연 저항 | Insulation Resistance | 절연저항 시험 | 일진전기 내부 |
| PI | 편극 지수 | Polarization Index | - | IEEE 43 |

## 생산팀 (10개)

| 표준 용어 | 한글 용어 | 영문 용어 | 현재 사용 | 출처 |
|----------|----------|----------|----------|------|
| VPD | 진공 가압 건조 | Vacuum Pressure Drying | 진공건조 | IEC 60076 |
| 권선권취 | - | Coil winding | 권선감기 | 내부자료 |
| 진공건조 | - | Vacuum drying | - | 내부자료 |
| 침지 | - | Impregnation | 함침 | 내부자료 |
| 와인딩기계 | 권선기 | Winding machine | 권선기 | 내부자료 |
| 용접 | - | Welding | - | 내부자료 |
| CO2용접기 | 이산화탄소용접기 | CO2 welding machine | CO2 용접기 | 내부자료 |
| 아크용접기 | - | Arc welding machine | 아크 용접기 | 내부자료 |
| 조립 | - | Assembly | 조립작업 | 내부자료 |
| 탱크제작 | - | Tank fabrication | 외함제작 | 내부자료 |

## 개발팀 (10개)

| 표준 용어 | 한글 용어 | 영문 용어 | 현재 사용 | 출처 |
|----------|----------|----------|----------|------|
| AIAG-VDA | - | AIAG-VDA FMEA Handbook | AIAG-VDA 2019 | 국제 표준 |
| AP | 조치 우선순위 | Action Priority | H/M/L | AIAG-VDA |
| FCM | 고장 원인-메커니즘-모드 | Failure Cause-Mechanism-Mode | - | AIAG-VDA |
| PFMEA | 공정 FMEA | Process Failure Mode and Effects Analysis | 프로세스 FMEA | AIAG-VDA |
| 고장 형태 | - | Failure Mode | 변형/크랙/부식/과열/단락/누유/소음/진동 등 (구체적 현상) | 회의 합의 |
| 고장 원인 | - | Failure Cause | 설계불량/재료불량/제작불량/시험불량/운송불량/설치불량/운영불량 | AIAG-VDA |
| 고장 영향 | - | Failure Effect | 5가지 영향 (시스템/상위/제품/정부/사용자) | AIAG-VDA |
| 노이즈 인자 | - | Noise Factor | 5대 노이즈 (외부환경/고객사용/시스템상호작용/시간경과/부품간변동) | AIAG-VDA |
| CAD | - | Computer-Aided Design | CAD | 외부자료 |
| CAE | - | Computer-Aided Engineering | CAE | 외부자료 |

## 시공팀 (10개)

| 표준 용어 | 한글 용어 | 영문 용어 | 현재 사용 | 출처 |
|----------|----------|----------|----------|------|
| 설치 | - | Installation | - | 외부자료 |
| 시운전 | - | Commissioning | - | 외부자료 |
| 운송 | - | Transportation | 배송 | 외부자료 |
| 현장조립 | - | Site assembly | - | 외부자료 |
| 기초 | - | Foundation | - | 외부자료 |
| 접지 | - | Grounding | - | EEPortal Glossary |
| 누설시험 | - | Leakage test | 누설시험 | 외부자료 |
| 압력시험 | - | Pressure test | 압력시험 | 외부자료 |
| 오일주입 | - | Oil filling | 충진 | 외부자료 |
| 현장검수 | - | Site inspection | 현장검수 | 외부자료 |

## 구매팀 (10개)

| 표준 용어 | 한글 용어 | 영문 용어 | 현재 사용 | 출처 |
|----------|----------|----------|----------|------|
| 발주 | - | Purchase order | 발주서 | 내부자료 |
| 납품 | - | Delivery | - | 내부자료 |
| 협력사 | - | Supplier | 협력업체 | 내부자료 |
| 자재출고 | - | Material issue | 자재불출 | 내부자료 |
| 원자재 | - | Raw material | - | 내부자료 |
| 구매품 | - | Purchased item | - | 내부자료 |
| 검수 | - | Receiving inspection | 입고검수 | 내부자료 |
| 재고 | - | Inventory | - | 내부자료 |
| 납기관리 | - | Delivery management, Delivery control | 납기관리 | 내부자료 |
| 견적 | - | Quotation | 견적요청 | 내부자료 |

## 프로젝트관리팀 (10개)

| 표준 용어 | 한글 용어 | 영문 용어 | 현재 사용 | 출처 |
|----------|----------|----------|----------|------|
| 일정 | - | Schedule | - | 내부자료 |
| 회의 | - | Meeting | - | 내부자료 |
| 보고서 | - | Report | - | 내부자료 |
| 승인 | - | Approval | - | 내부자료 |
| 변경관리 | 변경통제 | Change management | 변경관리 | 내부자료 |
| 리스크 | 위험관리 | Risk management | 리스크 | 내부자료 |
| 문서관리 | - | Document control | - | 내부자료 |
| 작업흐름 | - | Workflow | Work flow | 내부자료 |
| 이슈 | - | Issue | - | 내부자료 |
| 프로젝트 | - | Project | - | 내부자료 |

## 국제표준 (10개)

| 표준 용어 | 한글 용어 | 영문 용어 | 현재 사용 | 출처 |
|----------|----------|----------|----------|------|
| IEC 60076 | - | IEC 60076 Power Transformers | IEC 60076 시리즈 | IEC |
| IEEE C57.12 | - | IEEE C57.12 Transformer Standards | IEEE 변압기 표준 | IEEE |
| CIGRE TB 642 | - | CIGRE Technical Brochure 642 | 변압기 고장 통계 | CIGRE |
| IEC 60214 | - | IEC 60214 Tap Changers | OLTC 표준 | IEC |
| IEC 60296 | - | IEC 60296 Insulating Oil | 절연유 표준 | IEC |
| IEC 60599 | - | IEC 60599 DGA Interpretation | DGA 해석 기준 | IEC |
| CRGO | 냉간 압연 방향성 규소강판 | Cold Rolled Grain Oriented | 방향성 규소강판 | 철강 업계 |
| Step-lap | 단계 적층 | Step-lap Core | 스텝랩 | 변압기 업계 |
| DCWR | 직류 권선 저항 | DC Winding Resistance | 직류 저항 | IEC 60076 |
| ONAN | 유입자연대류냉각 | Oil Natural Air Natural | 자연대류냉각, ONAN | 외부자료 |
