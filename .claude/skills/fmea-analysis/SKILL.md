---
name: fmea-analysis
description: 변압기 FMEA 전문가. AIAG-VDA 2019 통합 방식, MCP 도구 기반 자동 검증. Use when (1) Creating transformer FMEA, (2) Analyzing failure modes, (3) Generating Excel templates
---

## 스킬 경로 상수 (BLOCKING!)

| 경로 | 절대경로 |
|------|----------|
| SKILL_DIR | `C:\Users\jmyoo\.claude\skills\fmea-analysis` |
| SCRIPT_DIR | `C:\Users\jmyoo\.claude\skills\fmea-analysis\scripts` |
| REFERENCES_DIR | `C:\Users\jmyoo\.claude\skills\fmea-analysis\references` |
| EXCEL_SCRIPT | `C:\Users\jmyoo\.claude\skills\fmea-analysis\scripts\generate_fmea_excel.py` |
| AGENTS_DIR | `c:\Users\jmyoo\Desktop\FMEA\.claude\agents` |
| LEADER_PLAYBOOK | `c:\Users\jmyoo\Desktop\FMEA\.claude\agents\fmea-leader.md` |

> [X] 금지: `scripts/generate_fmea_excel.py` 상대경로 사용
> [X] 금지: `find`/`Glob`으로 스크립트 검색 후 커스텀 대체물 작성
> [O] 필수: 위 EXCEL_SCRIPT 절대경로로 직접 실행!

---

## [!] MCP 도구 필수 사용

> **[BLOCKING]** 모든 FMEA 항목은 MCP 도구로 검증 후 생성!
> **[!]** MCP 도구는 deferred tools! `ToolSearch("fmea")` 호출로 먼저 로드해야 사용 가능!

| MCP 도구 | 용도 | 시점 |
|---------|------|------|
| `ToolSearch` | MCP 도구 로드 (deferred tools) | 모든 MCP 호출 전 |
| `fmea_validate_failure_mode` | E열 금지어/태그 검증 | 항목 작성 전 |
| `fmea_validate_effect` | C열 물리상태 금지어 검증 | 항목 작성 전 |
| `fmea_validate_cause` | F열 라이프사이클 태그 검증 | 항목 작성 전 |
| `fmea_validate_mechanism` | G열 화살표 형식 검증 | 항목 작성 전 |
| `fmea_validate_prevention` | H열 줄 수 검증 | 항목 작성 전 |
| `fmea_validate_detection` | J열 줄 수 검증 | 항목 작성 전 |
| `fmea_validate_causal_chain` | E-F 인과관계 검증 | 항목 작성 전 |
| `fmea_validate_batch` | 배치 JSON 전체 검증 | Excel 생성 전 |
| `fmea_create_item` | 항목 생성 (출처 검증 포함) | **v13: Generator 미사용** |
| `fmea_register_read` | 파일 Read 등록 (환각방지) | Read 직후 |
| `fmea_check_read_status` | 필수 파일 Read 확인 | 항목 작성 전 |
| `fmea_get_forbidden_words` | 금지어 목록 조회 | 필요시 |

---

## 워크플로우 (Subagent 병렬 실행)

> [!!] 스킬 활성화 시 fmea-leader.md를 Read하고 playbook으로 따름!

```
1. Read(LEADER_PLAYBOOK)                     <- 절대경로 필수!
   c:\Users\jmyoo\Desktop\FMEA\.claude\agents\fmea-leader.md
2. fmea-leader.md의 Phase 0~3 지시를 따름   <- playbook!
3. Task(subagent_type=..., mode="dontAsk") 패턴 사용
```

> [!!] fmea-leader.md는 spawn 대상이 아님! 메인 세션이 Read하고 playbook으로 따름!

### Agent 파일 (AGENTS_DIR: `c:\Users\jmyoo\Desktop\FMEA\.claude\agents\`)

| Agent | 역할 | model | 사용 방법 |
|-------|------|-------|-----------|
| `fmea-leader` | playbook (메인 세션이 Read) | sonnet | Read -> 지시 따름 |
| `fmea-worker-collector` | 데이터 수집 (A+D/B/C) | haiku | Task(subagent_type=...) |
| `fmea-worker-generator` | FMEA 항목 생성 + 4-Round 병렬 사전검증 | sonnet | Task(subagent_type=...) |
| `fmea-worker-fixer` | 보완/수정 (다이아몬드/라이프사이클/용어) | haiku | Task(subagent_type=...) |

### 4-Round 병렬 사전검증 순서 (Phase 2 핵심! v13 성능최적화)

```
[Round 1] 독립 검증 4개 병렬 (1 LLM turn!)
  fmea_validate_failure_mode(E) + fmea_validate_cause(F)
  fmea_validate_mechanism(G)    + fmea_validate_effect(C)

[Round 2] 교차 검증 5개 병렬 (1 LLM turn!)
  fmea_validate_causal_chain(E,F) + fmea_validate_cause_mechanism(F,G)
  fmea_validate_function_effect(B,C)
  fmea_validate_prevention(H,cause=F) + fmea_validate_detection(J,mode=E)

[Round 3] fmea_validate_row_context(B,C,E,F,G,H,J)
[Round 4] S/O/D + RPN + AP 산출 (MCP 불요)
```
> fmea_create_item() 미사용 (Round 1-3 전수 검증으로 대체)

### 상세 규칙: [subagent-rules.md](references/agent-teams-rules.md)

---

## 출력 폴더 구조 (CRITICAL!)

> **중간 파일은 `_work/` 서브폴더에, 최종 결과만 메인 폴더에!**

```
03.FMEA/{카테고리}/{부품명}/
+-- _work/                        <- 모든 중간 파일
|   +-- worker_a_diagram.json     (Worker A+D 결과 - 다이어그램)
|   +-- worker_b_docs.json        (Worker B 결과 - 이 1개만!)
|   +-- worker_c_docs.json        (Worker C 결과 - 제작/시험)
|   +-- rules_summary.json        (Worker A+D 결과 - 온톨로지)
|   +-- research_data.json        (Leader 통합 데이터)
|   +-- worker1_{effect}.json     (Phase 2 Worker 결과)
|   +-- worker2_{effect}.json
|   +-- (fix scripts if any)
+-- {부품명}_FMEA_batch1.json     <- 최종 배치 JSON
+-- {부품명}_FMEA_batch2.json
+-- {부품명}_FMEA_combined.json   <- 통합 JSON
+-- {도면명}_FMEA.xlsx            <- Excel (최종 결과물)
```

**[X] 금지**: Worker가 메인 폴더에 중간 파일 직접 생성
**[X] 금지**: Worker B가 SUMMARY.md, INDEX.md, EXECUTION_REPORT.txt 등 부가 파일 생성

---

## STEP 0: 기능분석 다이어그램 + 용어사전

**다이어그램**: `01.회의/00.회의 자료/02.다이어그램_기능분석/변압기_FMEA_Step2_Step3_다이어그램_v2.9_xlsx.json`
**용어사전**: `01.회의/00.회의 자료/01.용어정리/변압기_전문용어집_V2.2_xlsx.json`

```
1. Read(다이어그램_v2.9_xlsx.json)
   -> sheets.기능분석 배열에서 부품명 검색
   -> E열(L3)=부품명, F열=기능
2. Read(전문용어집_V2.2_xlsx.json) -> 표준 용어 확인
3. Glob(카테고리 폴더) -> 없으면 mkdir
```

**상세**: [function-analysis.md](references/function-analysis.md)

---

## STEP 1: 내부문서 + WebSearch

> **[SUBAGENT]** `fmea-worker-collector` (Worker B + Worker C) + Leader WebSearch

```python
# Worker B: 설계+재료 문서
Task(subagent_type="fmea-worker-collector", mode="dontAsk",
     prompt="Worker B: 부품명={부품명}. 설계+재료 내부문서 Read. "
            "mandatory_docs_by_component.json에서 design[]+material[] 경로 추출 후 Read.")

# Worker C: 제작+시험 문서
Task(subagent_type="fmea-worker-collector", mode="dontAsk",
     prompt="Worker C: 부품명={부품명}. 제작+시험 내부문서 Read. "
            "mandatory_docs_by_component.json에서 manufacturing[]+testing[] 경로 추출 후 Read.")

# Leader(메인 세션)가 WebSearch 직접 수행 (서브에이전트 불가!)
```

**순서**: 인덱스 조회 -> Worker B(설계+재료) + Worker C(제작+시험) 병렬 -> Leader WebSearch

| 담당 | mandatory_docs 키 | 문서 유형 | H/J 작성 |
|------|-------------------|---------|---------|
| Worker B | design[] | CHECK (.json), WORKFLOW (.json), TD (.md) | 설계 단계 |
| Worker B | design[]/testing[] | R시리즈 (.md) | 재료 단계 |
| Worker C | manufacturing[] | W시리즈 (.md), I시리즈 (.md) | 제작 단계 |
| Worker C | testing[] | P시리즈 (.md) | 시험 단계 |
| Leader | - | WebSearch 5개 | 외부 표준 |

**[!] 변환 파일 Read**: `_converted/` 하위 텍스트 파일 (MD/JSON) 직접 Read!

**Read 후 즉시 등록** (환각 방지!):
```python
fmea_register_read(file_path, content_hash)
```

**상세**: [mandatory-docs.md](references/mandatory-docs.md)

---

## STEP 1.5: 온톨로지 규칙 로드

> **[SUBAGENT]** `fmea-worker-collector` (Worker A+D) - 다이어그램 + 온톨로지 병합

```python
Task(subagent_type="fmea-worker-collector", mode="dontAsk",
     prompt="Worker A+D: 부품목록={부품목록}. "
            "다이어그램 F열 추출 + 온톨로지 6개 파일 로드. "
            "_work/worker_a_diagram.json + _work/rules_summary.json 저장.")
```

**로드 파일** (references/ 실제 파일명!):
- failure-mode-ontology.md (E열 금지어/태그 규칙)
- effect-ontology.md (C열 물리상태 금지어 규칙)
- causal-chain-ontology.md (F열+G열 인과관계/금지조합 규칙)
- diamond-structure.md (다이아몬드 구조 필수요건)
- column-details.md (컬럼별 상세 형식 규칙)
- prevention-detection-ontology.md (H열+J열 출처/기준값 규칙)

---

## STEP 2: FMEA 항목 완성

> **[MCP 검증 필수]** 모든 항목은 MCP 도구로 검증!

**작성 순서**:
```
Round 1 (병렬): E열->validate_failure_mode + F열->validate_cause + G열->validate_mechanism + C열->validate_effect
Round 2 (병렬): E-F->causal_chain + F-G->cause_mechanism + B-C->function_effect + H->prevention + J->detection
Round 3: row_context 행맥락 검증
Round 4: S/O/D + RPN + AP 산출 (MCP 불요)
배치 완료: fmea_validate_batch()
```

**필수 형식**:

| 컬럼 | 형식 | MCP 검증 |
|------|------|---------|
| E열 | `부족:/과도:/유해: 현상` | `fmea_validate_failure_mode` |
| F열 | `설계:/재료:/제작:/시험: 원인` | `fmea_validate_cause` |
| G열 | `원인 -> 과정 -> 결과` (화살표 2개+) | `fmea_validate_mechanism` |
| H열 | 4줄 이상 | `fmea_validate_prevention` |
| J열 | 4줄 이상 | `fmea_validate_detection` |

**상세**: [ghj-format-rules.md](references/ghj-format-rules.md), [cef-format-rules.md](references/cef-format-rules.md)

---

## STEP 3: Excel 생성

```bash
python "$USERPROFILE/.claude/skills/fmea-analysis/scripts/generate_fmea_excel.py" {batch_path}
```

> [X] 금지: 커스텀 Python 스크립트 작성 (openpyxl/pandas 직접 사용)
> [O] 필수: 위 EXCEL_SCRIPT 절대경로만 사용!

**입력**: 배치 JSON (fmea_validate_batch 통과)
**출력**: Excel 파일 (FMEA 양식)

**GATE 4 체크**:
- 기능 커버리지 (모든 기능 >= 1항목, 주기능 >= 30%) **(v12 신규!)**
- 라이프사이클 균형 (설계/재료/제작/시험 각 1개+)
- 다이아몬드 구조 (형태당 원인 2개+)

---

## 절대 금지 [BLOCKING]

| 금지 | 이유 | MCP 검증 |
|------|------|---------|
| E열에 피로/응력집중/크리프 | 메커니즘! | `fmea_validate_failure_mode` |
| E열에 소음/진동/증가/저하 | 미래결과/측정값! | `fmea_validate_failure_mode` |
| C열에 이완/변형/균열 | 물리적 상태! | `fmea_validate_effect` |
| F열 태그 없음 | 라이프사이클 필수! | `fmea_validate_cause` |
| G열 화살표 1개만 | 2개 이상 필수! | `fmea_validate_mechanism` |
| H/J열 3줄 이하 | 4줄 이상 필수! | `fmea_validate_prevention/detection` |
| Read 없이 인용 | 환각! | `fmea_check_read_status` |
| 주기능 누락 | 기능 커버리지! | GATE 4 (v12) |
| 이모지 사용 | cp949 오류! | ASCII만 사용 |

---

## 참조 파일

| 파일 | 내용 |
|------|------|
| [failure-mode-ontology.md](references/failure-mode-ontology.md) | E열 금지어 SSOT |
| [effect-ontology.md](references/effect-ontology.md) | C열 금지어 SSOT |
| [diamond-structure.md](references/diamond-structure.md) | 다이아몬드 구조 |
| [ghj-format-rules.md](references/ghj-format-rules.md) | G/H/J열 형식 |
| [cef-format-rules.md](references/cef-format-rules.md) | C/E/F열 형식 |
| [anti-hallucination.md](references/anti-hallucination.md) | 환각 방지 원칙 |
| [workflow.md](references/workflow.md) | 워크플로우 상세 |

---

**버전**: 2.6-Subagent
**최종 수정**: 2026-02-08
**변경사항**: v12 - 기능 커버리지 GATE, F-G 연동 검증, Worker C 절대경로, SOD 형식 통일, 복합어 예외 동기화
