# Anti-Hallucination Guide (Grounded Response)

> **[ABSOLUTE]** AI가 문서를 읽지 않고 내용을 날조(fabrication)하는 것을 방지하는 필수 가이드

---

## [!!] PRIMARY 원칙: Read-Write 동기화 (ABSOLUTE!)

> **[ABSOLUTE]** 이 규칙이 모든 anti-hallucination 규칙의 기반!
> **근본 원인**: 문서를 읽고 나중에 작성하면 컨텍스트에서 사라져 날조 발생

### 핵심
**"파일 Read 직후 바로 해당 내용으로 FMEA H/J열 작성"**

### 올바른 패턴
```
CHECK SHEET Read -> [즉시] H/J 설계 단계 작성 -> 작업표준 Read -> [즉시] H/J 제작 단계 작성 -> ...
```

### 잘못된 패턴 (날조 발생!)
```
CHECK SHEET Read -> 작업표준 Read -> 시험요령 Read -> ... -> [나중에] H/J열 한꺼번에 작성
```

### 라이프사이클별 Read-Write 순서
| 순서 | Read 문서 | 즉시 작성 |
|------|----------|----------|
| 1 | 설계: CHECK SHEET, WORKFLOW, DRAWING, TD | H/J 설계 단계 |
| 2 | 제작: W시리즈, I시리즈, C시리즈 | H/J 제작 단계 |
| 3 | 시험: P시리즈 | H/J 시험 단계 |
| 4 | 재료: R시리즈 | H/J 재료 단계 |

**[X] 금지**: 모든 문서 다 읽고 나서 H/J열 한꺼번에 작성!

---

## [!!] 핵심 원칙: Read-Before-Write

**절대 규칙**: 파일을 Read 도구로 열지 않은 상태에서 해당 파일의 내용을 인용하거나 작성하는 것은 **금지**!

```
[X] 금지 행동:
1. 인덱스만 보고 파일 내용 추측
2. 일반 지식으로 내부 문서 내용 가정
3. WebSearch 없이 "검색 결과" 작성
4. 실제 문서의 섹션 번호를 추측으로 작성

[OK] 올바른 행동:
1. Read 도구로 실제 파일 열기
2. 파일 내용에서 직접 복사
3. WebSearch 실제 실행 후 URL과 함께 인용
4. 실제 문서에서 섹션 번호 확인 후 작성
```

---

## [LOCK] 출처 작성 시 필수 검증 (CITATION VERIFICATION)

### 1. 내부 문서 출처 작성 규칙

**[BLOCKING]** 내부 문서를 출처로 인용하려면 반드시:

| 단계 | 필수 행동 | 검증 방법 |
|------|----------|----------|
| 1 | Read 도구로 해당 파일 열기 | Read 기록에 파일명 있어야 함 |
| 2 | 실제 섹션/항목 번호 확인 | 문서 내에서 직접 복사 |
| 3 | 내용이 일치하는지 확인 | 작성 내용 = 문서 내용 |

### 2. 실제 문서 형식 vs 잘못된 형식

> **[!!] CRITICAL**: 실제 일진전기 문서의 형식을 반드시 확인 후 인용!

**문서별 실제 형식 예시**:

| 문서 유형 | 잘못된 형식 (추측) | 올바른 형식 (실제) | 확인 방법 |
|----------|------------------|-------------------|----------|
| 작업표준(W) | `W030 S3.1` | `W030 순서3`, `W030 10.1항` | Read 후 목차 확인 |
| 수입검사(R) | `R012 3.2` | 실제 문서 구조에 따름 | Read 후 구조 확인 |
| CHECK SHEET | `권선CS-No.5` | `권선 CHECK SHEET 권선-No.5` | Read 후 정확한 명칭 확인 |
| 도시바TD | `TD4 p.78` | Read 후 페이지 내용 확인 | 해당 페이지 실제 Read |

### 3. 출처 작성 전 자가 검증 체크리스트

```
출처 작성 전 반드시 확인:

[ ] 이 파일을 Read 도구로 실제로 열었는가?
[ ] 인용하는 섹션/항목 번호가 실제 문서에 존재하는가?
[ ] 작성하는 내용이 실제 문서 내용과 일치하는가?
[ ] 문서의 형식(순서#, #항, S#.# 등)이 실제와 일치하는가?

하나라도 "아니오"면 -> 해당 출처 사용 금지!
```

---

## [MANDATORY] Read 기록 테이블 (필수 출력)

> **[BLOCKING]** FMEA 작성 시 반드시 Read 기록 테이블 출력 필수!

### 형식

```markdown
## [DATA] Read 기록 테이블

| 순서 | Read 시점 | 파일 경로 | 추출 정보 | FMEA 사용 컬럼 |
|------|----------|----------|----------|---------------|
| 1 | STEP 0 | .../기능분석_다이어그램.xlsx | 기능 5개 | B열 |
| 2 | STEP 1 | .../IEQT-T-W030.pdf | 순서3 압착조건 | H열 |
| 3 | STEP 1 | .../단자_CHECK_SHEET.xlsm | 검사항목 8개 | J열 |
```

### 출처-Read 매칭 검증

**[LOCK]** FMEA에서 인용한 출처는 반드시 Read 기록에 있어야 함!

```
예시:
H열에 "(W030 순서3)" 작성
-> Read 기록에 "IEQT-T-W030.pdf" 있어야 함
-> 없으면 해당 출처 사용 금지!
```

---

## [BLOCKING] WebSearch 출처 규칙

### 1. WebSearch 실행 필수

**[X] 금지**: WebSearch 실행 없이 "검색 결과"를 작성
**[OK] 필수**: 실제 WebSearch 도구 실행 후 결과 인용

### 2. WebSearch 기록 형식

```markdown
## [DATA] WebSearch 기록

| 검색어 | 검색 결과 URL | 추출 정보 | FMEA 사용 |
|-------|-------------|----------|----------|
| "IEC 60076 terminal" | https://... | 단자 요구사항 | F열, G열 |
| "transformer bushing failure" | https://... | 고장 통계 | O열 |
```

### 3. 검색 결과 없는 경우 처리

| 상황 | 처리 방법 | 출처 표기 |
|------|----------|----------|
| 검색 결과 있음 | URL과 함께 인용 | `(IEC 60076-5 S8.2)` |
| 검색 결과 없음 | Claude 지식 명시 | `(Claude 지식 - 검증 필요)` |
| 불확실한 정보 | 추정임을 명시 | `(추정 - 내부 확인 필요)` |

**[!] 주의**: `(Claude 지식)` 표기 항목은 신뢰도가 낮음 - 사용자에게 검증 권고

---

## [ABSOLUTE] 날조 금지 패턴

### 1. 절대 금지 행동

| 금지 행동 | 결과 | 올바른 방법 |
|----------|------|------------|
| 읽지 않은 파일 내용 작성 | **Fabrication!** | Read 후 작성 |
| 존재하지 않는 섹션 번호 인용 | **False Citation!** | 실제 번호 확인 |
| WebSearch 없이 검색 결과 작성 | **Fabrication!** | 실제 검색 실행 |
| 추측으로 기준값 작성 | **Inaccurate Data!** | 문서에서 추출 |

### 2. 날조 검출 패턴

**[!] 다음 패턴은 날조 가능성 높음**:

```
- S#.# 형식 (일진전기 문서에서 드묾)
- 정확한 숫자가 있으나 출처 없음
- 통계 데이터가 있으나 URL 없음
- 여러 출처가 완벽하게 정렬됨 (너무 깔끔함)
```

---

## [TOOL] 검증 함수 추가 예정

### validate_citations.py (구현 예정)

```python
def validate_citations(fmea_data: dict, read_log: list) -> dict:
    """
    FMEA에서 인용한 출처가 실제 Read된 문서에 있는지 검증

    Parameters:
    - fmea_data: FMEA 데이터 (JSON)
    - read_log: Read 기록 (파일 경로 목록)

    Returns:
    - {'valid': bool, 'errors': list}
    """
    errors = []

    for item in fmea_data['items']:
        # H열, J열에서 출처 추출
        h_citations = extract_citations(item.get('현재예방대책', ''))
        j_citations = extract_citations(item.get('현재검출대책', ''))

        for citation in h_citations + j_citations:
            if citation['type'] == 'internal':
                # 내부문서 출처가 Read 로그에 있는지 확인
                if not any(citation['doc_id'] in f for f in read_log):
                    errors.append({
                        'type': 'UNREAD_CITATION',
                        'citation': citation['raw'],
                        'message': f"출처 '{citation['doc_id']}'가 Read 기록에 없음!"
                    })

    return {'valid': len(errors) == 0, 'errors': errors}
```

---

## [REF] 관련 문서

- [workflow.md](workflow.md) - GATE 0 Read 검증
- [column-details.md](column-details.md) - H열/J열 출처 표기
- [internal-docs-index.md](internal-docs-index.md) - 내부 문서 인덱스
- [websearch-mandatory.md](websearch-mandatory.md) - WebSearch 규칙

---

**버전**: 1.0
**작성일**: 2026-01-28
**목적**: AI Hallucination/Fabrication 방지
