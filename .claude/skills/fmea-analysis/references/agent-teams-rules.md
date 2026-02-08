# Subagent BLOCKING Rules

> 권선자재표 실행 분석 결과 도출된 재발방지 규칙 (260207, Subagent 전환 260208)

## 1. Subagent 필수 사용 (BLOCKING)

FMEA 작성 시 반드시 Subagent 패턴을 사용해야 합니다.

```
[X] 금지: generic Task(subagent_type="general-purpose") 사용
[X] 금지: 메인 Claude가 직접 STEP 0~3 순차 실행
[X] 금지: Task(subagent_type="fmea-leader") spawn! (Leader는 spawn 대상 아님!)
[X] 금지: Agent Teams API (TeamCreate/SendMessage/TeamDelete)
[O] 필수: Read(".claude/agents/fmea-leader.md") -> playbook으로 따름
[O] 필수: 메인 세션이 Leader 역할 수행 (Task(subagent_type=..., mode="dontAsk"))
```

> [!!] fmea-leader.md는 spawn 대상이 아님! 메인 세션이 Read하고 playbook 지시를 따름!

---

## 2. 출력 폴더 구조 (BLOCKING)

```
03.FMEA/{카테고리}/{부품명}/
+-- _work/                        <- 모든 중간 파일
|   +-- worker_a_diagram.json    (Worker A+D - 다이어그램)
|   +-- worker_b_docs.json       (Worker B 유일 출력!)
|   +-- worker_c_docs.json       (Worker C - 제작/시험)
|   +-- rules_summary.json       (Worker A+D - 온톨로지)
|   +-- research_data.json
|   +-- worker1_{effect}.json    (Phase 2)
|   +-- worker2_{effect}.json
+-- {부품명}_FMEA_batch1.json     <- 최종 배치
+-- {부품명}_FMEA_combined.json   <- 통합
+-- {도면명}_FMEA.xlsx            <- Excel
```

**금지사항**:
- Worker가 메인 폴더에 중간 파일 생성
- Worker B가 SUMMARY.md, INDEX.md, EXECUTION_REPORT.txt 등 부가 파일 생성
- fix 스크립트를 메인 폴더에 생성 (필요시 _work/에만)

---

## 3. Worker B 출력 제한 (BLOCKING)

Worker B(내부문서-설계/재료)는 **worker_b_docs.json 1개만** 출력합니다.

```
[X] 금지 출력물:
  - EXECUTION_REPORT.txt
  - INDEX.md
  - WORKER_B_SUMMARY.md
  - 개별 문서 요약 JSON
  - 기타 부가 파일

[O] 유일 출력물:
  _work/worker_b_docs.json = {
    "internal_docs": {...},
    "read_status": {...},
    "extracted_data": {...}
  }
```

---

## 4. Phase 2 MCP 4-Round 병렬 사전검증 (BLOCKING, v13 성능최적화)

Worker(fmea-worker-generator)는 항목 1개씩 생성할 때 **반드시** 4-Round 병렬 MCP 사전검증을 실행합니다.

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

**금지**: MCP 검증 없이 항목을 JSON에 직접 작성
**근거**: MCP 사전검증 미실행 시 Phase 3에서 10+ 재시도 cascade 발생

---

## 5. Phase 3 오류 수정: fmea-worker-fixer 필수 호출 (BLOCKING)

generate_fmea_excel.py는 ALL-AT-ONCE 모드로 모든 BLOCKING 오류를 한 번에 보고합니다.
Leader는 이 오류 목록 전체를 fmea-worker-fixer에 전달하여 일괄 수정합니다.

```
[X] 금지: 오류 1개씩 수동 fix 스크립트 작성
[X] 금지: sed/awk로 JSON 직접 편집
[O] 필수: fmea-worker-fixer Worker에 전체 오류 목록 전달
```

**fixer Worker 전달 형식** (Subagent 패턴):
```
Task(subagent_type="fmea-worker-fixer",
     mode="dontAsk",
     prompt="ALL-AT-ONCE 오류 목록: {Excel 검증 오류 전문}. "
            "batch JSON: {path}. rules_summary: {path}.")
```

---

## 6. 사전검증 재시도 제한

- Worker 내 MCP 검증 실패: 최대 3회 재시도
- 3회 실패: 실패 사유를 JSON의 statistics.escalations에 기록, 해당 항목 스킵 후 계속
- Leader 판단: fixer Worker 할당 또는 수동 지시

---

> 이하 규칙은 내용정리.txt #2 (권선자재표 15부품 세션) 분석에서 도출 (260207)

## 7. 커스텀 스크립트 생성 금지 (BLOCKING)

```
[X] 금지: Python 스크립트 직접 작성 (openpyxl, pandas 등)
[X] 금지: generate_excel.py, create_sample_fmea.py 등 커스텀 파일 생성
[X] 금지: Bash(command="python -c '...'")로 Excel/JSON 생성 로직 작성
[O] 필수: 스킬 스크립트만 사용!
```

**EXCEL_SCRIPT 경로 (프로젝트 루트 기준)**:
`.claude/skills/fmea-analysis/scripts/generate_fmea_excel.py`

**근거**: 커스텀 스크립트는 컬럼 매핑(A~V), 셀 병합(A-E), 정렬 규칙을 모두 무시함
-> 내용정리.txt #2: B열=잠재원인(오류), C열=원인/메커니즘(오류) 등 컬럼 완전 불일치

---

## 8. MCP 도구 ToolSearch 필수 (BLOCKING)

MCP 도구(fmea_validate_*)는 **deferred tools**. 사용 전 반드시 로드!

```
ToolSearch("fmea") -> 16개 도구 로드

[X] 금지: ToolSearch 없이 MCP 도구 호출 시도
[X] 금지: "pre_validated", "검증 통과 간주" 등 가짜 검증 상태
[O] 필수: Leader/Generator/Fixer 모두 ToolSearch 호출 후 MCP 사용
```

**근거**: 내용정리.txt #2에서 MCP 4-Round 0회 실행 -> 항목 품질 0%

---

## 9. 완료 전 BLOCKING 체크 (거짓 완료 방지!)

Leader는 완료 보고 전 반드시 확인:

```
[ ] 1. 전체 부품 수 == 처리된 부품 수 (다이어그램 기준)
[ ] 2. batch JSON 파일 Glob 존재 확인
[ ] 3. Excel이 EXCEL_SCRIPT로 생성됐는지 확인
[ ] 4. 처리 안 된 부품이 있으면 "미완료" 보고 (PASS 금지!)

[X] 금지: 부분 완료를 전체 완료(PASS)로 보고
[X] 금지: "샘플" "일부" 처리 후 완료 보고
```

**근거**: 내용정리.txt #2에서 15개 부품 중 3개만 처리 후 "GATE 4 PASS" 보고

---

## 10. 온톨로지/스크립트 경로 (BLOCKING)

스킬 파일은 프로젝트 `.claude/skills/fmea-analysis/`에 위치!

```
스킬 기본 경로: .claude/skills/fmea-analysis/

[X] 금지: 02.참고자료/ 하위에서 온톨로지 검색
[X] 금지: 프로젝트 폴더에서 find/Glob으로 스크립트 검색
[O] 필수: 아래 경로로 직접 접근!
```

**온톨로지 6개 파일 경로 (프로젝트 루트 기준)**:
1. `.claude/skills/fmea-analysis/references/failure-mode-ontology.md`
2. `.claude/skills/fmea-analysis/references/effect-ontology.md`
3. `.claude/skills/fmea-analysis/references/diamond-structure.md`
4. `.claude/skills/fmea-analysis/references/column-details.md`
5. `.claude/skills/fmea-analysis/references/prevention-detection-ontology.md`
6. `.claude/skills/fmea-analysis/references/causal-chain-ontology.md`

**근거**: 내용정리.txt #2에서 Worker D가 `02.참고자료/01.Claude/스킬/` 경로 검색 -> FileNotFoundError
