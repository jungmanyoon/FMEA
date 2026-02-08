---
name: fmea-leader
description: FMEA Leader Playbook. 전체 워크플로우 조율, Worker 분배, 결과 병합, GATE 검증. Phase 1(데이터수집) -> Phase 2(FMEA생성+사전검증) -> Phase 3(최종검증+Excel). Subagent 패턴 사용.
model: sonnet
---

# FMEA Leader Playbook (Subagent 패턴)

## 역할
FMEA 전체 워크플로우의 총괄 조율자. **메인 세션이 이 파일의 지시를 따름.**

> [!!] 이 파일은 subagent로 spawn하지 않음! 메인 세션이 직접 Leader 역할 수행!
> [!!] Task(subagent_type=...) 패턴 사용. Agent Teams API(TeamCreate/SendMessage/TeamDelete) 사용 안 함!

## [!] MCP 도구 (ToolSearch 로드 필요)
MCP 도구는 deferred tools. 사용 전 `ToolSearch("fmea")` 호출로 로드.
스킬 경로/스크립트/온톨로지는 preloaded skill(fmea-analysis)에서 참조.

## FMEA TFT 팀원 이름 매핑

| 역할 | Phase 1 (수집) | Phase 2 (생성) | Phase 3 (수정) |
|------|---------------|---------------|---------------|
| Collector A+D | 다이어그램+온톨로지 | - | - |
| Collector B | 내부문서-설계/재료 | - | - |
| Collector C | 내부문서-제작/시험 | - | - |
| **Leader** | **WebSearch 5회 (직접 수행)** | 조율/검증 | Excel 생성 |
| Generator 1~N | - | 고장영향별 항목 생성 | - |
| Fixer | - | - | ALL-AT-ONCE 수정 |

> [!] Phase 2 generator 수: 고장영향 수에 따라 동적 결정 (2~4개)
> [!] 10항목 미만 영향은 인접 영향과 병합하여 Worker 수 최소화
> [!!] WebSearch는 서브에이전트에서 시스템 레벨 제한! Leader가 직접 수행!

## [X] 절대 금지 (BLOCKING)
- [X] 금지: Python 스크립트 직접 작성 (create_sample_fmea.py, generate_excel.py 등)
- [X] 금지: openpyxl/pandas 직접 import하여 Excel 생성
- [X] 금지: "샘플"/"일부" 처리 후 전체 완료(PASS) 보고
- [X] 금지: Agent Teams API 사용 (TeamCreate/SendMessage/TeamDelete)
- [O] 필수: EXCEL_SCRIPT 절대경로로 Excel 생성!
- [O] 필수: 전체 부품 수 == 처리 부품 수 확인 후에만 완료 보고!

---

## Phase 0: 사전 준비

### L-0.1 작업 폴더 확인/생성
```
[!!] Glob은 파일만 매칭! 디렉토리 존재 확인은 Bash ls 사용!
Bash: ls "03.FMEA/{카테고리}/" | grep "^{도면명}"
기존 폴더 있으면 -> 번호 증가 (예: _2, _3, _4)
추가: _work/ 서브폴더도 생성!
```
> [!] 폴더 구조: 중간 파일은 `_work/`에, 최종 결과만 메인 폴더!
> [X] 금지: Glob으로 디렉토리 존재 확인 (파일 0개 폴더 = 미발견!)

---

## Phase 1: 데이터 수집 (3 Workers + Leader WebSearch 동시)

### L-1.0 Leader WebSearch 직접 수행 (Workers와 병렬!)
> [!!] WebSearch는 서브에이전트에서 시스템 레벨 제한! Leader가 직접 수행!
```python
# Leader가 직접 WebSearch 5회 수행 (Workers 생성과 동시 실행!)
WebSearch("transformer winding insulation material failure mode FMEA IEC 60076")
WebSearch("power transformer insulation barrier cylinder spacer failure analysis IEEE")
WebSearch("transformer winding insulation material degradation root cause CIGRE")
WebSearch("변압기 권선 절연자재 고장 사례 분석")
WebSearch("transformer winding spacer block strip insulation defect prevention detection")
# -> 결과를 _work/leader_websearch.json에 저장
```

### L-1.1 3개 Worker 동시 생성 (CRITICAL!)

> [!!] 반드시 mode="dontAsk" 포함! (Worker 도구 권한 요청이 메인 UI로 전달 안됨!)
> [!!] Worker A+D 병합: 다이어그램 추출 + 온톨로지 로드를 1개 Worker가 수행!

```python
# 3개 Worker를 Subagent로 동시 생성!

# Worker A+D: 다이어그램 추출 + 온톨로지 로드 (병합!)
Task(subagent_type="fmea-worker-collector",
     mode="dontAsk",
     prompt="Worker A+D: 다이어그램 F열 추출 + 온톨로지 6개 로드. "
            "부품명: {부품명}. 작업폴더: {work_path}")

# Worker B: 내부문서 전반 (설계+재료 문서)
Task(subagent_type="fmea-worker-collector",
     mode="dontAsk",
     prompt="Worker B: 내부문서 Read (설계+재료). "
            "mandatory_docs에서 design[], material[] 문서만 Read. "
            "CHECK SHEET, WORKFLOW, TD시리즈, R시리즈 담당. "
            "출력: worker_b_docs.json. 작업폴더: {work_path}")

# Worker C: 내부문서 후반 (제작+시험 문서)
Task(subagent_type="fmea-worker-collector",
     mode="dontAsk",
     prompt="Worker C: 내부문서 Read (제작+시험). "
            "mandatory_docs에서 manufacturing[], testing[] 문서만 Read. "
            "W시리즈, I시리즈, P시리즈 담당. "
            "출력: worker_c_docs.json. 작업폴더: {work_path}")
```

### L-1.2 결과 수신
- Subagent 반환값으로 직접 수신 (SendMessage 불필요!)
- _work/ 폴더의 worker_*.json 파일 확인
- **Worker A+D**: worker_a_diagram.json + rules_summary.json
- **Worker B**: worker_b_docs.json (설계+재료)
- **Worker C**: worker_c_docs.json (제작+시험)
- **Leader**: leader_websearch.json (WebSearch - Leader가 직접 저장)

### L-1.3 결과 통합
- Worker A+D + B + C + Leader WebSearch -> research_data.json 병합 저장
- rules_summary.json 저장 확인

### L-1.4 GATE 0 자동 검증
```
fmea_check_read_status() 호출
-> 미충족 시: 누락 문서 재수집 Worker 추가 실행 (최대 3회)
-> 3회 실패 시: 가용한 데이터로 계속 진행 (누락 항목 로그 남김)
-> 충족 시: 자동으로 Phase 2 진행
```

### L-1.5 기능 목록 자동 확정
- Worker A+D 결과 (다이어그램 기능) + Worker B/C 내부문서 + Leader WebSearch 추가 기능 후보 병합
- [!!] 다이어그램 기능 = 전부 MANDATORY! 1개도 누락 불가! (BLOCKING!)
- [!!] 내부문서/WebSearch에서 추가 기능 발굴 시 function list에 추가!
- [!!] 사용자 확인 없이 자동 확정 후 Phase 2 진행!
- [!!] 주기능/보조기능 구분 필수! 다이어그램 첫번째 기능 = 주기능!

### L-1.5.1 기능별 항목 할당 계획 (BLOCKING! v12.1 강화)
> [!!] 다이어그램 모든 기능 = 각 최소 2개 항목! (1개만 = 불충분!)
> [!!] 내부문서/WebSearch 추가 기능 = 각 최소 1개 항목!
```
기능 할당 규칙 (v12.1 강화):
1. 다이어그램 기능 (주기능+보조기능 전부): 각 최소 2개 항목! (BLOCKING!)
   -> 주기능: 전체 항목의 >= 30% 할당 (최소 2개, 권장 4개+)
   -> 보조기능: 각 최소 2개 항목 (= 최소 1 고장형태 x 2 원인)
   -> 0개 기능 = BLOCKING FAIL! 자동 재생성!
2. 추가 기능 (내부문서/WebSearch 발굴): 각 최소 1개 항목
3. function_coverage_plan을 research_data.json에 포함!
   예: {"F1_주기능": {"min_items": 4, "type": "주기능", "source": "다이어그램"},
        "F2_보조기능": {"min_items": 2, "type": "보조기능", "source": "다이어그램"},
        "F3_추가기능": {"min_items": 1, "type": "추가기능", "source": "내부문서"}}
4. Generator 프롬프트에 function_coverage_plan 전달!
```

### L-1.6 고장영향 목록 확정 + 공통 데이터 사전 생성
- 고장영향별 S값 맵 확정
- [!!] 고장영향 상세설명 확정 (C열 셀 병합 필수! v14 신규)
  -> 각 고장영향에 "영향\n(상세설명)" 2줄 형식으로 확정!
  -> 같은 고장영향 = 모든 항목에서 동일한 상세설명! (고장형태별 분기 금지!)
  -> 상세설명은 고장형태에 종속되지 않는 범용 설명으로 작성!
  -> 예: "전류 통전 불가\n(리드 접속부 통전 경로 차단으로 전류 흐름 불가)"
  -> [X] 금지: "전류 통전 불가\n(열변형으로 인한...)" (고장형태 맥락 혼입!)
- 기능-고장영향 매핑 테이블 생성
- 공통 데이터 사전: standard_expressions, s_value_map, function_effect_map, effect_descriptions, doc_numbers, units

---

## Phase 2: FMEA 생성 (고장영향별 Workers)

### L-2.0 MCP 도구 로드
```python
ToolSearch("fmea")  # MCP 도구 로드 (deferred tools)
```

### L-2.1 Generator Workers 생성
> [!!] 10항목 미만 고장영향은 인접 영향과 병합하여 Worker 수 최소화!
> [!!] 각 Generator에 research_data 전체가 아닌 **해당 고장영향 관련 데이터만** 전달!

```python
# 고장영향별 Worker 동시 생성 (컨텍스트 최소화!)
# 해당 영향 관련 데이터만 추출하여 전달
relevant_data_1 = extract_by_effect(research_data, "절연파괴")

Task(subagent_type="fmea-worker-generator",
     mode="dontAsk",
     prompt="고장영향: {영향_상세설명포함}(S={S값}). 부품명: {부품명}. "
            "[!!] C열은 전달받은 고장영향 문자열을 그대로 사용! 상세설명 변경 금지! "
            "관련 기능: {function_effect_map에서 해당 영향만 추출}. "
            "[!!] 기능 커버리지 필수! function_coverage_plan: {할당계획}. "
            "주기능 '{주기능명}'에 최소 {N}개 항목 생성! "
            "작업폴더: {work_path}. "
            "research_data(해당 영향 관련만): {relevant_data}. "
            "rules_summary: {path}. "
            "공통데이터사전: {사전 내용}")

Task(subagent_type="fmea-worker-generator",
     mode="dontAsk",
     prompt="고장영향: {영향2}(S={S값}). ...")
# ... 필요한 수만큼
```
> [!!] Generator 프롬프트에 function_coverage_plan 반드시 포함! 주기능 누락 방지!

### L-2.2 결과 수신 + 키 정규화 + 병합
- Subagent 반환값으로 직접 수신
- 파일 확인: _work/gen*_{effect}.json
- [!!] 키 정규화 스크립트 실행 (영어 키 -> 한글 키 자동 변환!)
```bash
python "$USERPROFILE/.claude/skills/fmea-analysis/scripts/normalize_gen_keys.py" {work_path} --output {combined_path} --category {카테고리} --drawing {도면명}
```
- 정규화 후 postprocessor 실행:
```bash
python "$USERPROFILE/.claude/skills/fmea-analysis/scripts/postprocess_fmea.py" {combined_path}
```
> [!!] normalize_gen_keys.py가 project_info 키도 자동 생성! 수동 추가 불필요!
> [!!] Generator가 영어 키(part, B, C, E, F, G, H, J)를 출력해도 자동 변환됨!

### L-2.3 배치 분리
- {도면명}_FMEA_batch{N}.json 저장 (메인 폴더에!)

### L-2.4 배치 검증
```python
fmea_validate_batch(json_content)  # 전체 검증
```

### L-2.5 기능 커버리지 검증 (BLOCKING! v12.1 강화)
> [!!] 다이어그램 모든 기능이 batch에 각 2개+ 항목으로 출현하는지 확인!
```
검증 절차:
1. research_data.json의 functions[] 목록 추출 (source별 구분!)
2. batch JSON의 모든 항목에서 '기능' 값 수집 + 기능별 항목 수 집계
3. 다이어그램 기능 중 0개 항목 -> BLOCKING! Generator Worker 추가 실행!
4. 다이어그램 기능 중 1개 항목 -> WARNING! 최소 2개로 보강 권고!
5. 추가기능(내부문서/WebSearch) 중 0개 항목 -> WARNING + 추가 생성 권고
6. 주기능이 전체의 30% 미만이면 -> WARNING + 추가 생성 권고
```

### L-2.6 전체 구조 검증
- 기능 커버리지: 다이어그램 기능 전부 각 2개+ 항목 (BLOCKING!)
- 추가기능: 각 1개+ 항목 (WARNING)
- 주기능 비율: 전체 항목의 >= 30% (WARNING)
- 다이아몬드: 형태당 원인 2개 이상
- 라이프사이클: 설계/재료/제작/시험 각 15% 이상
- 미달 시: Phase 3 보완 Worker 실행

### L-2.8 batch JSON 존재 확인 (BLOCKING!)
```
Glob("03.FMEA/{카테고리}/{도면명}*/*_FMEA_batch*.json")
-> 0개: Phase 2 미완료! Worker 재실행 필요!
```

---

## Phase 3: 최종 검증 + Excel 생성

### L-3.1 Excel 1차 시도
```bash
python "$USERPROFILE/.claude/skills/fmea-analysis/scripts/generate_fmea_excel.py" {batch_path}
```

### L-3.2 오류 시 Fixer 생성
```python
# ALL-AT-ONCE 오류 목록 전체를 fixer 1개에 전달 (통합!)
Task(subagent_type="fmea-worker-fixer",
     mode="dontAsk",
     prompt="ALL-AT-ONCE 오류 목록: {Excel 검증 오류 전문}. "
            "batch JSON: {path}. rules_summary: {path}. "
            "다이아몬드 미달 형태: {목록}. 라이프사이클 부족 단계: {목록}. "
            "[!!] F열 변경 시 G열 연동 검증 필수! fmea_validate_cause_mechanism() 재검증!")
```

### L-3.3 보완 병합 + Excel 재생성
- Fixer 결과 수신 (Subagent 반환값)
- batch JSON 업데이트
- generate_fmea_excel.py 재실행

### L-3.5 GATE 4 검증
- 입력 안내 메시지 22개 (A6~V6)
- Row 5 높이 = 40
- 20개 컬럼 값 존재
- A-E 컬럼 병합 완료

### L-3.5.5 완료 전 자동 BLOCKING 체크
```
자동 검증 (통과 시 L-3.6으로 진행, 미통과 시 자동 재시도):
1. 전체 부품 수 == 처리된 부품 수? -> 미달 시 누락 부품 자동 재생성
2. batch JSON 파일 존재? -> 없으면 Phase 2 재실행
3. Excel이 EXCEL_SCRIPT로 생성됐는지? -> 미생성 시 자동 재실행
```

### L-3.6 완료 보고
```
== FMEA 완료 ==
부품명: {부품명}
총 항목: {N}개
배치 수: {M}개
Workers: Phase1={3}개 + Phase2={N}개 + Phase3={0~1}개
Phase 1: {시간}분
Phase 2: {시간}분
Phase 3: {시간}분
전체: {총시간}분
Excel: {경로}
```

---

## [!] 핵심 원칙

### Subagent 패턴 (BLOCKING!)
- Task(subagent_type=..., mode="dontAsk"): Workers를 Subagent로 생성
- 결과는 반환값 + JSON 파일로 수신 (SendMessage 불필요!)
- Worker 종료 자동 (shutdown 프로토콜 불필요!)

> [!!] mode="dontAsk" 필수! Worker의 도구 권한 요청이 메인 UI로 전달 안됨!
> [!!] WebSearch는 서브에이전트에서 시스템 레벨 제한! Leader만 직접 수행 가능!

### Worker 분배 원칙
- Phase 1: 3 collector Workers (A+D병합/B설계재료/C제작시험) + Leader WebSearch
- Phase 2: 2~4 generator Workers (고장영향별, 소규모 영향 병합)
- Phase 3: 필요시 1 fixer Worker (ALL-AT-ONCE 통합)

### 컨텍스트 최소화 원칙 (토큰 절감!)
- Generator에 research_data 전체 전달 금지!
- 해당 고장영향 관련 데이터만 추출하여 전달
- 공통 데이터 사전은 간결하게 요약
