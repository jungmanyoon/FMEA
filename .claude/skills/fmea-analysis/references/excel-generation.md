# Excel 생성 필수 알고리즘

**AIAG-VDA 2019 FMEA Excel 파일 결정적 생성 가이드**

---

## [LIST] 출력 파일 구조 (2개 시트)

**생성되는 Excel 파일**:
```
{부품명}_FMEA.xlsx
├── Sheet 1: 기능분석 (AIAG-VDA Step 3)
│   - 구분, 파트명, 주기능, 보조기능, 관련 고장형태, 고장영향
│   - FMEA 데이터에서 자동 추출 (중복 제거)
│
└── Sheet 2: FMEA (AIAG-VDA Step 4-6)
    - 20개 컬럼 (기존 구조 유지)
    - 셀 병합, AP 색상, 입력 안내 메시지 포함
```

**기능분석 시트 목적**: AIAG-VDA 7-Step에서 Step 3(기능 분석)을 별도로 문서화
- 각 부품의 주기능과 보조기능 정의
- 기능과 고장형태/고장영향 연결 관계 명확화
- 상세 가이드: [function-analysis.md](function-analysis.md)

---

## 📑 목차

1. [[!] 문제와 해결책](#️-문제와-해결책)
2. [1단계: 데이터 구조 사전 계획](#1단계-데이터-구조-사전-계획)
3. [2단계: 셀 병합 알고리즘](#2단계-셀-병합-알고리즘)
4. [3단계: 빈 셀 방지](#3단계-빈-셀-방지)
5. [3-1단계: 논리적 일관성 검증](#3-1단계-논리적-일관성-검증)
6. [4단계: 일관성 보장](#4단계-일관성-보장)
7. [Excel 생성 전체 절차](#excel-생성-전체-절차)
8. [필수 준수 사항 (CRITICAL)](#필수-준수-사항-critical)
9. [이전 문제 해결 매핑](#이전-문제-해결-매핑)
10. [직접 openpyxl 코딩 시 완전한 예제](#직접-openpyxl-코딩-시-완전한-예제)

---

## [!] 문제와 해결책

**문제**:
- 매번 다른 결과
- 셀 병합 오류
- 빈 셀 발생

**해결**:
- 결정적 생성 알고리즘
- 검증 단계

---

## 1단계: 데이터 구조 사전 계획

### [LOCK] JSON 파일 구조 - 필수!

> **[BLOCKING]** 스크립트가 특정 JSON 구조를 기대합니다. 구조 오류 시 파싱 실패!

**최상위 키 이름**:
```json
{
  "fmea_data": [...],      // [OK] 필수! 스크립트가 이 키 이름을 기대
  "project_info": {        // [OK] 필수! Row 1 제목 생성에 사용
    "도면명": "단자 자재표"  // [BLOCKING] 필수! 다이어그램 D열에서 추출
  },
  "metadata": {...}        // [OK] 선택
}
```

### [BLOCKING] project_info.도면명 필수 규칙 (다이어그램 D열)

> **Excel Row 1 제목 = `{도면명}_FMEA`**
> **Excel 파일명 = `{도면명}_FMEA.xlsx`**
>
> `project_info.도면명`은 다이어그램 D열(L2 도면명)에서 추출!

**다이어그램 컬럼 구조**:
| 컬럼 | 헤더 | 용도 | 예시 |
|------|------|------|------|
| D열 | L2 (도면명) | Excel 파일명/Row 1 제목 | 단자 자재표, 철심, 권선 |
| E열 | L3 (부품명) | FMEA A열 (개별 부품) | 압착단자, 슬리브, CLAMP |
| F열 | 기능 | FMEA B열 | [목적어]를 [동사]한다 |

**올바른 예시**:
```json
{
  "project_info": {
    "도면명": "단자 자재표"   // -> 파일명: "단자 자재표_FMEA.xlsx", Row 1: "단자 자재표_FMEA"
  }
}
```

**잘못된 예시**:
```json
{
  "project_info": {
    "부품": "압착단자"       // [X] E열(부품명)을 사용 -> D열(도면명) 사용해야!
  }
}
```

**도면명 추출 절차**:
1. 다이어그램 파일 Read: `변압기_FMEA_Step2_Step3_다이어그램_v2.9_xlsx.json`
2. 기능분석 시트 **D열**(L2 도면명)에서 도면명 확인
3. `project_info.도면명`에 D열 값 입력

| 올바른 키 | 잘못된 키 |
|----------|----------|
| `fmea_data` | `fmea_items`, `items`, `data` |

### [LOCK] JSON 키 이름 - 한글 필수!

> **[BLOCKING]** 스크립트가 **한글 키 이름**을 기대합니다. 영어 키 사용 시 파싱 실패!

| 올바른 키 (한글) | 잘못된 키 (영어) |
|-----------------|-----------------|
| `부품명` | `part`, `part_name` |
| `기능` | `function` |
| `고장영향` | `failure_effect`, `effect` |
| `고장형태` | `failure_mode`, `mode` |
| `고장원인` | `failure_cause`, `cause` |
| `고장메커니즘` | `mechanism` |
| `현재예방대책` | `current_prevention`, `prevention` |
| `현재검출대책` | `current_detection`, `detection_measure` |
| `severity` | `severity` (예외: 숫자값이므로 영어 허용) |
| `occurrence` | `occurrence` (예외) |
| `detection` | `detection` (예외) |

**FMEA 항목을 먼저 완전한 데이터 구조로 생성**:

```python
# 데이터 구조 예시
fmea_data = [
    {
        "부품명": "CORE",
        "기능": "자속 전달",
        "기능_순서": 1,  # [!!] 다이어그램 순서 (CRITICAL!)
        "고장영향": "전압 변환 불가",
        "S": 10,
        "고장형태": "층간단락",
        "고장원인": "설계: 철심 재질 열화",
        "고장메커니즘": "자기 특성 저하 → 자속밀도 감소",
        "현재예방대책": "재료: 고효율 규소강판 사용 (CRGO 0.27mm)",
        "O": 2,
        "현재검출대책": "시험: 무부하 손실 측정 (FAT)",
        "D": 3,
        "AP": "L",
        # ... 나머지 컬럼
    },
    # ... 다음 항목
]
```

### [BLOCKING] 기능_순서 필드 필수!

> **[CRITICAL]** 다이어그램 순서를 Excel에서 유지하려면 `기능_순서` 필드 필수!
> 이 필드가 없으면 기능이 **문자열 알파벳 순**으로 정렬되어 다이어그램 순서가 깨짐!

**다이어그램 -> JSON 변환 시**:
```python
# 다이어그램에서 기능 추출 시 순서 번호 부여
functions_in_diagram = [
    {"기능": "전류의 경로를 제공한다", "기능_순서": 1},
    {"기능": "전류를 흘려 자기장을 만든다", "기능_순서": 2},
    {"기능": "자기장을 받아 전압을 발생시킨다", "기능_순서": 3},
    # ... 다이어그램 행 순서대로
]
```

**[X] 금지**: `기능_순서` 없이 JSON 생성 -> 기능 순서 깨짐!
**[O] 필수**: 다이어그램 Row 순서 = `기능_순서` 값

### 데이터 표기 형식 규칙 (CRITICAL!)

**[!] 매번 다른 결과 방지**: 아래 형식을 **엄격히** 준수해야 일관된 결과 생성!

**1. 부품명**:
- [OK] `"CORE"`, `"WINDING"`, `"BUSHING"`
- [X] `"부품 1: CORE"`, `"1. CORE"`

**2. 기능**:
- [OK] `"자속 전달"`, `"전압 변환"`, `"절연 유지"`
- [X] `"기능 1: 자속 전달"`, `"1. 자속 전달"`

**3. 고장영향** - **옵션 A 필수 적용**:
- [OK] `"전압 변환 불가\n(자속 밀도 저하로 2차측 출력 불가)"`
- [OK] `"권선 소손\n(과열로 인한 권선 절연 파괴)"`
- [X] `"고장영향 1: 전압 변환 불가"`, `"영향 1: 전압 변환 불가"`
- [X] `"1: 전압 변환 불가"`, `"① 전압 변환 불가"`

**4. 고장형태** (구체적 현상으로 작성) - [*] **3줄 구조 필수**:
- [OK] **옵션 A (3줄 구조: 현상 + 상세설명 + 태그 판단 근거)** (가이드 V1.3):
  - `"부족: 적층이완\n(철심 판의 누적 팽창으로 조립이 불안정한 상태)\n(부족: 전달된 자속이 부족하면 적층이완 발생)"`
  - `"과도: 포화흔적\n(자속 밀도 초과로 인한 철심 변색 현상)\n(과도: 전달된 자속이 과하면 포화흔적 발생)"`
  - `"유해: 와전류흔적\n(자속 전달 시 철심에서 발생하는 국부 발열 현상)\n(유해: 전달된 자속 정상 수행 시 의도치 않은 와전류흔적 발생)"`
- [X] `"고장형태 1: 층간단락"`, `"모드: 과열"`
- [X] `"부족"`, `"저하"`, `"과도"` **← 추상적 표현 금지!**
  - **이유**: 드러나는 현상으로 구체적 기술 필요
  - **참조**: [failure-mode-diversity.md](failure-mode-diversity.md) 부품별 목록

**3줄 구조 형식** (**대괄호 금지!**, 가이드 V1.3):
```
1줄: 부족: 현상 (또는 과도: / 유해:)
2줄: (현상에 대한 상세 설명)
3줄: (부족: [기능 결과물]이 부족하면 [현상] 발생)
```

> **[!!] 핵심 원리**: 태그 기준 = **기능 자체가 아닌 "기능이 만들어내는 결과물"**

**태그 판단 기준 (가이드 V1.3)**:
| 태그 | 핵심 질문 | 3줄 판단 근거 형식 |
|------|----------|-------------------|
| **부족:** | "기능 결과물이 부족하면?" | `(부족: [기능 결과물]이 부족하면 [현상] 발생)` |
| **과도:** | "기능 결과물이 과하면?" | `(과도: [기능 결과물]이 과하면 [현상] 발생)` |
| **유해:** | "기능 결과물 정상인데 부작용?" | `(유해: [기능 결과물] 정상 수행 시 의도치 않은 [현상] 발생)` |

**5. 고장원인** (`[단계]: [설명]` 형식 + **옵션 A 필수 적용**):
- [OK] `"설계: 철심 적층두께 설계 오류\n(설계값 대비 실제 두께 부족)"`
- [OK] `"제작: 압착력 부족\n(목표 2500kN에 1800kN 미달)"`
- [X] `"원인 1: 설계: 철심 재질 열화"`, `"1. 설계: 철심 재질 열화"`
- [X] `"철심 재질 열화"` (단계 누락)

**[!] 핵심**: **번호, 접두사, 라벨 절대 금지!** 내용만 써야 함!

**정렬 순서 (CRITICAL)** - 병합 계층 구조와 일치해야 함!:
1. 부품명 (알파벳/한글 순) - 병합 계층 1
2. **기능_순서 (다이어그램 순서!)** - 병합 계층 2 [*] **[BLOCKING] 문자열 순 금지!**
3. 고장영향 (문자열 순) - 병합 계층 3 [*] 필수!
4. **심각도 S (내림차순)** - 같은 고장영향 내에서
5. 고장형태 (문자열 순) - 병합 계층 5
6. 고장원인 (라이프사이클 단계 순: 1.설계→2.재료→3.제작→4.시험)

**[!] 주의**: 기능과 고장영향이 정렬 키에 없으면 다이아몬드 구조 병합 불가!

> **[!!] CRITICAL - 기능 정렬**:
> - **[X] 금지**: `row['기능']` (문자열 순) -> 다이어그램 순서 깨짐!
> - **[O] 필수**: `row.get('기능_순서', 999)` (다이어그램 Row 순서)

**정렬 알고리즘**:
```python
def sort_fmea_data(data):
    """FMEA 데이터 결정적 정렬 - 병합 계층 구조와 일치 + 다이어그램 순서 보존"""

    # 라이프사이클 단계 순서 (4단계)
    lifecycle_order = {
        '설계': 1, '재료': 2, '제작': 3, '시험': 4
    }

    def sort_key(row):
        # 고장원인에서 라이프사이클 단계 추출
        lifecycle_stage = row['고장원인'].split(':')[0].strip()

        return (
            row['부품명'],                                      # 1. 부품명 (병합 계층 1)
            row.get('기능_순서', 999),                          # 2. [!!] 기능_순서 (다이어그램 순서!) - 문자열 순 금지!
            row['고장영향'],                                    # 3. 고장영향 (병합 계층 3) [*]
            -row['S'],                                          # 4. S (내림차순)
            row['고장형태'],                                    # 5. 고장형태 (병합 계층 5)
            lifecycle_order.get(lifecycle_stage, 99),          # 6. 라이프사이클 단계 순서
            row['고장원인']                                     # 7. 고장원인 (문자열 순)
        )

    return sorted(data, key=sort_key)
```

**[!] 필수**: Excel 생성 전에 **반드시** 이 정렬 함수를 적용해야 셀 병합이 정상 작동합니다.

**[BLOCKING] 기능_순서 미포함 시 오류 발생**:
```python
# 검증 코드 (generate_fmea_excel.py에 포함됨)
for item in fmea_data:
    if '기능_순서' not in item:
        print(f"[WARNING] 기능_순서 누락! 기능: {item['기능']} -> 다이어그램 순서 확인 필요!")
```

---

## 2단계: 셀 병합 알고리즘

**병합 조건 정의** (정렬 순서와 일치!):

```python
# 컬럼별 병합 조건 (부품명→기능→고장영향→S→고장형태)
# [OK] 정렬도 같은 순서: 부품명→기능→고장영향→S→고장형태
#    이 순서가 일치해야 다이아몬드 구조 병합 가능!
merge_rules = {
    "A": "부품명",    # 전체 행에서 같은 부품명이면 병합
    "B": "기능",      # 같은 부품 내에서 같은 기능이면 병합
    "C": "고장영향",  # 같은 기능 내에서 같은 영향이면 병합
    "D": "S",         # 같은 영향에 대해 병합 (영향당 S값은 고정)
    "E": "고장형태",  # 같은 영향 내에서 같은 모드면 병합
}

# 병합하지 않는 컬럼 (F-T)
no_merge = ["고장원인", "고장메커니즘", "O", "D", "AP", "예방조치", ...]
```

**병합 로직**:

```python
def apply_cell_merge(ws, data, start_row=7):
    """셀 병합 적용 (컬럼 A-E만)"""

    # 1. 컬럼 A (부품명) 병합
    merge_column(ws, 'A', start_row, data, key="부품명")

    # 2. 컬럼 B (기능) 병합 - 같은 부품 내에서
    merge_column(ws, 'B', start_row, data, key="기능", parent="부품명")

    # 3. 컬럼 C (고장영향) 병합 - 같은 기능 내에서
    merge_column(ws, 'C', start_row, data, key="고장영향", parent="기능")

    # 4. 컬럼 D (S) 병합 - 같은 영향에 대해
    merge_column(ws, 'D', start_row, data, key="S", parent="고장영향")

    # 5. 컬럼 E (고장형태) 병합 - 같은 영향 내에서
    merge_column(ws, 'E', start_row, data, key="고장형태", parent="고장영향")

def merge_column(ws, col, start_row, data, key, parent=None):
    """단일 컬럼 병합 로직"""
    i = start_row
    while i < start_row + len(data):
        # 연속된 같은 값 찾기
        merge_start = i
        current_value = data[i - start_row][key]

        # parent 조건 확인 (있는 경우)
        if parent:
            parent_value = data[i - start_row][parent]

        j = i + 1
        while j < start_row + len(data):
            # 같은 값이고, parent가 같은 경우만 병합
            if data[j - start_row][key] == current_value:
                if parent is None or data[j - start_row][parent] == parent_value:
                    j += 1
                else:
                    break
            else:
                break

        # 병합 실행 (2개 이상 행만)
        if j - i > 1:
            ws.merge_cells(f'{col}{i}:{col}{j-1}')
            ws[f'{col}{i}'].alignment = Alignment(vertical='center')

        i = j
```

---

## 3단계: 빈 셀 방지

**필수 검증**:

```python
def validate_data(data):
    """빈 셀 방지 및 형식 검증 (STEP 1-5: A~M열만)"""
    import re

    # [!!] 스킬 범위: STEP 1-5 (리스크 분석)만 담당
    # N~V열(조치계획 + 개선 후)은 빈값으로 유지
    required_columns = [
        # 현재 상태 (A~M열, 1-13번) - 필수!
        "부품명", "기능", "고장영향", "S", "고장형태",
        "고장원인", "고장메커니즘", "현재예방대책", "O",
        "현재검출대책", "D", "RPN", "AP"
        # N~V열(14-22번): 빈값 유지 - 스킬 범위 밖
    ]

    # 1. 빈 값 검증 (A~M열만)
    for i, row in enumerate(data):
        for col in required_columns:
            if not row.get(col) or row[col] == "":
                raise ValueError(f"행 {i+1}, 컬럼 '{col}': 빈 값 불허")

    # 2. 형식 검증 (번호 표기 금지!)
    for i, row in enumerate(data):
        # 번호 패턴 검출: "기능 1:", "고장영향 1:", "①", "1.", "1:" 등
        number_patterns = [
            r'^(기능|고장영향|고장형태|고장원인|영향|모드|원인)\s*\d+\s*:',  # "기능 1:", "고장영향 2:"
            r'^\d+\s*[:.)]',  # "1:", "1.", "1)"
            r'^[①②③④⑤⑥⑦⑧⑨⑩]',  # 원 숫자
        ]

        for col in ['기능', '고장영향', '고장형태']:
            value = str(row.get(col, ''))
            for pattern in number_patterns:
                if re.match(pattern, value):
                    raise ValueError(f"행 {i+1}, 컬럼 '{col}': 번호 표기 금지! 내용만 써야 함. 값: '{value}'")

        # 고장형태는 구체적 현상이어야 함 (추상적 표현 금지)
        invalid_modes = ['부재', '부족', '과도', '간헐', '의도하지않음', '저하', '지연', '역효과']
        if row['고장형태'] in invalid_modes:
            raise ValueError(f"행 {i+1}, 고장형태는 구체적 현상으로 작성! (층간단락, 과열, 변형 등): {row['고장형태']}")

        # 고장원인은 "[단계]: [설명]" 형식이어야 함
        if ':' not in str(row['고장원인']):
            raise ValueError(f"행 {i+1}, 고장원인은 '[단계]: [설명]' 형식이어야 함: {row['고장원인']}")

        lifecycle_stage = str(row['고장원인']).split(':')[0].strip()
        valid_stages = ['설계', '재료', '제작', '시험']
        if lifecycle_stage not in valid_stages:
            raise ValueError(f"행 {i+1}, 고장원인 단계는 4단계 중 하나여야 함: {lifecycle_stage}")

    return True
```

**빈 값 처리 규칙**:

> **[!] 스킬 범위**: STEP 1-5 (리스크 분석)까지만 담당
> N~V열(조치계획 + 개선 후)은 **빈값으로 유지**

| 컬럼 범위 | 내용 | 스킬 처리 |
|----------|------|----------|
| **A~M열 (1-13번)** | 현재 상태 | **필수 작성** |
| **N~Q열 (14-17번)** | 조치 계획 | 빈값 유지 |
| **R~V열 (18-22번)** | 개선 후 | 빈값 유지 |

**N~V열 빈값 처리**:
```python
# [!!] STEP 6 (최적화)는 스킬 범위 밖
# N~V열은 추후 담당자가 별도 입력

# 14-17. 조치 계획 (N~Q열) - 빈값
예방조치 = ""   # N열
검출조치 = ""   # O열
담당자 = ""     # P열
목표일 = ""     # Q열

# 18-22. 개선 후 (R~V열) - 빈값
S_prime = ""    # R열
O_prime = ""    # S열
D_prime = ""    # T열
RPN_prime = ""  # U열
AP_prime = ""   # V열
```

---

## 3-1단계: 논리적 일관성 검증

**[!] 필수 검증**: validate_data() 후 실행

```python
def validate_logical_consistency(data):
    """논리적 일관성 및 개별성 검증"""

    # 1. H~T열 반복 검증 (CRITICAL!)
    seen_combinations = {}
    for i, row in enumerate(data):
        # 고장원인 + 예방조치 + 검출조치 조합
        key = (row['고장원인'], row['예방조치'], row['검출조치'])

        if key in seen_combinations:
            prev_idx = seen_combinations[key]
            raise ValueError(
                f"[!] H~T열 반복 발견!\n"
                f"행 {prev_idx+1}과 행 {i+1}이 동일한 대책:\n"
                f"  고장원인: {row['고장원인']}\n"
                f"  예방조치: {row['예방조치']}\n"
                f"  검출조치: {row['검출조치']}\n"
                f"→ 각 항목마다 다른 대책을 생성해야 합니다!"
            )
        seen_combinations[key] = i

    # 2. 담당자 논리적 검증
    담당자_매핑 = {
        '설계': ['전기설계팀', '구조설계팀', '개발팀'],
        '재료': ['구매팀', 'QA팀', '전기설계팀', '구조설계팀'],
        '제작': ['생산팀', '생산기획팀'],
        '시험': ['QA팀', '시험팀']
    }

    for i, row in enumerate(data):
        lifecycle_stage = row['고장원인'].split(':')[0].strip()
        expected_teams = 담당자_매핑.get(lifecycle_stage, [])
        actual_team = row['담당자']

        # 담당자가 예상 팀 중 하나를 포함하는지 확인
        if not any(team in actual_team for team in expected_teams):
            raise ValueError(
                f"행 {i+1}: 담당자 불일치\n"
                f"  고장원인: {row['고장원인']}\n"
                f"  현재 담당자: {actual_team}\n"
                f"  예상 담당자: {'/'.join(expected_teams)}"
            )

    # 3. 예방조치/검출조치 구체성 검증
    generic_values = ['검토 중', '없음', '미정', 'TBD']

    for i, row in enumerate(data):
        # H 등급은 구체적 대책 필수
        if row['AP'] == 'H':
            if row['예방조치'] in generic_values:
                raise ValueError(
                    f"행 {i+1}: AP='H'인데 예방조치가 '{row['예방조치']}'\n"
                    f"  고장원인: {row['고장원인']}\n"
                    f"→ H 등급은 구체적인 예방조치 필수!"
                )

            if row['검출조치'] in generic_values:
                raise ValueError(
                    f"행 {i+1}: AP='H'인데 검출조치가 '{row['검출조치']}'\n"
                    f"  고장원인: {row['고장원인']}\n"
                    f"→ H 등급은 구체적인 검출조치 필수!"
                )

        # M 등급도 가급적 구체적 대책
        if row['AP'] == 'M':
            if row['예방조치'] in generic_values or row['검출조치'] in generic_values:
                print(
                    f"[!] 경고 - 행 {i+1}: AP='M'인데 대책이 비구체적\n"
                    f"  예방조치: {row['예방조치']}\n"
                    f"  검출조치: {row['검출조치']}"
                )

    # 4. 고장원인-메커니즘-대책 연결성 검증
    for i, row in enumerate(data):
        고장원인 = row['고장원인']
        예방조치 = row['예방조치']
        검출조치 = row['검출조치']

        # 설계 단계 원인인데 제작 대책 → 오류
        if "설계:" in 고장원인:
            if "작업 표준" in 예방조치 or "공정 관리" in 예방조치:
                raise ValueError(
                    f"행 {i+1}: 단계 불일치\n"
                    f"  고장원인: {고장원인} (설계 단계)\n"
                    f"  예방조치: {예방조치} (제작 단계 대책)\n"
                    f"→ 설계 원인은 설계 대책(Design Review, 설계 검증 등) 필요!"
                )

        # 제작 단계 원인인데 설계 대책 → 오류
        if "제작:" in 고장원인:
            if "Design Review" in 예방조치 and "공정" not in 예방조치:
                raise ValueError(
                    f"행 {i+1}: 단계 불일치\n"
                    f"  고장원인: {고장원인} (제작 단계)\n"
                    f"  예방조치: {예방조치} (설계 단계 대책)\n"
                    f"→ 제작 원인은 제작 대책(공정 관리, 작업 표준 등) 필요!"
                )

    print(f"[OK] 논리적 일관성 검증 통과 (총 {len(data)}개 항목)")
    return True
```

**검증 실행 순서**:
```python
# 1. 형식 검증
validate_data(fmea_data)

# 2. 논리적 일관성 검증
validate_logical_consistency(fmea_data)

# 3. Excel 생성 진행
```

---

## 4단계: 일관성 보장

**결정적 생성 체크리스트**:

- [ ] **고정된 정렬 순서**: 부품→기능→영향(S↓)→모드(표준순)→원인(단계순)
- [ ] **전체 컬럼 채우기**: 20개 컬럼 모두 값 존재 (13-20번은 기본값)
- [ ] **셀 병합 적용**: A-E 컬럼 (1-5번) 병합 완료
- [ ] **수직 중앙 정렬**: 병합된 모든 셀에 `vertical='center'` 적용
- [ ] **테두리 적용**: 모든 셀에 thin border 적용
- [ ] **헤더 색상**: Row 8 녹색 (#70AD47), Row 9 파란색 (#4472C4)
- [ ] **페이지 설정**: A3 가로, 1페이지에 모든 열 맞춤

**생성 후 검증**:

```python
def verify_excel(filename):
    """생성된 Excel 파일 검증"""
    wb = load_workbook(filename)
    ws = wb.active

    # 1. 병합된 셀 확인
    merged_ranges = ws.merged_cells.ranges
    print(f"병합된 셀 범위: {len(merged_ranges)}개")

    # 2. 빈 셀 확인 (전체 20개 컬럼)
    required_cols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
                     'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T']
    for row in range(9, ws.max_row + 1):
        for col in required_cols:
            value = ws[f'{col}{row}'].value
            if not value or value == "":
                print(f"[!] 빈 셀 발견: {col}{row}")

    # 3. 정렬 순서 확인
    # ...

    return True
```

---

## Excel 생성 전체 절차

**Claude 수행 절차 (반드시 순서대로)**:

### [준비 단계]
1. WebSearch 5개 출처 검색 (IEC/IEEE/CIGRE/Transformer Magazine/일반)
2. 실제 고장 형태 및 원인 추출 → 자연스럽게 항목 수 결정 (품질 우선, 개수 제한 없음)
3. 기능 분석 → 고장 형태 도출 → 원인 확대

### [데이터 생성 단계]
4. **완전한 데이터 구조 생성** (fmea_data 리스트)
   - 모든 항목을 dict 형태로 생성
   - 1-12번 컬럼 값 모두 채우기
   - 13-20번 컬럼은 기본값으로 자동 채우기

5. **13-20번 컬럼 기본값 채우기** (fill_default_values 함수)
   - 예방조치/검출조치: AP 기준 "검토 중" 또는 "없음"
   - 담당자: 라이프사이클 단계별 자동 매핑
   - 목표일: AP 기준 "즉시", "3개월", "6개월"
   - S'/O'/D'/AP': 초기값 자동 계산

6. **데이터 정렬 적용** (sort_fmea_data 함수 - CRITICAL!)
   - 부품명 → 기능 → 고장영향(S↓) → 고장형태(표준순) → 고장원인(단계순)
   - **[!] 이 단계를 건너뛰면 셀 병합이 작동하지 않음!**

7. **품질 검증** (validate_data 함수 - CRITICAL!)
   - 실제 위험 기반, 중복/무관 항목 배제
   - **전체 20개 컬럼** 빈 값 검사
   - **형식 검증**: 번호 표기 금지, 구체적 고장형태, 라이프사이클 단계 확인
   - **[!] 이 단계를 통과해야 일관된 결과 생성!**

### [Excel 생성 단계]
8. **Excel 파일 생성** (openpyxl 사용)
   - **[!] CRITICAL**: 데이터가 sort_fmea_data로 정렬되었는지 확인!
   - Row 1: 제목 "{부품명}_FMEA" (굵게, 16pt, 가운데 정렬, A1:T1 병합)
   - Row 2: "프로젝트: 변압기"
   - Row 3: "자료 출처: [실제 사용한 출처만 명시]" (예: IEC 60076-1, CIGRE TB 642, Claude 전문 지식)
   - [!] 주의: WebSearch로 실제 참조한 출처만 작성! 고정 템플릿 아님!
   - Row 4: 빈 행 (구분선 역할)
   - Row 5: AIAG-VDA 7-Step 프로세스 구분 (녹색 #70AD47, Step 2-6)
   - Row 6: 헤더 (파란색 #4472C4)
     - **[!!] 셀 메모 추가**: 각 헤더 셀(A6-T6)에 작성 가이드 메모 추가
     - openpyxl Comment 사용
     - 내용: [references/cell-comments.md](cell-comments.md) 참조
     - 크기: 매우 긴(500x350), 긴(450x300), 보통(400x250)
   - Row 7+: 정렬된 FMEA 데이터 (20개 컬럼 모두 채워짐)

9. **셀 병합 적용** (apply_cell_merge 함수, start_row=7)
   - 컬럼 A-E만 병합 (부품명, 기능, 고장영향, S, 고장형태)
   - 컬럼 F-T는 병합 금지

10. **서식 적용**
    - 병합 셀: 수직 중앙 정렬
    - 모든 셀: thin border
    - **행 높이 설정**: 데이터 행(Row 7+)에 충분한 높이 설정 (권장: 100)
    - 페이지 설정: A3 가로

11. **AP 컬럼 색상 적용** (AIAG-VDA 2019 표준)
    - L열(AP), T열(AP') 색상 코딩
    - H: 빨강 (#C00000), 흰색 굵은 글자
    - M: 노랑 (#FFC000), 흰색 굵은 글자
    - L: 녹색 (#92D050), 흰색 굵은 글자

12. **틀고정 적용** (`ws.freeze_panes = 'A7'`)
    - Row 1-6 고정 (제목, 출처, 헤더)
    - Row 7부터 스크롤 가능 (데이터)
    - 헤더가 항상 보이도록 유지

### [검증 단계]
13. **최종 검증** (verify_excel 함수)
    - 병합된 셀 범위 확인
    - **전체 20개 컬럼** 빈 셀 없는지 재확인
    - 정렬 순서 확인

14. **파일 저장** → {부품명}_FMEA.xlsx

---

## 필수 준수 사항 (CRITICAL)

- [OK] **결정적 생성**: 동일 부품은 항상 동일한 결과 (정렬 순서 고정)
- [OK] **정렬 순서**: 부품명 → 기능 → 고장영향 → **S(내림차순)** → 고장형태 → 고장원인
- [OK] **병합 계층과 일치**: 정렬 순서가 병합 계층(부품명→기능→고장영향)과 일치해야 함!
- [OK] **데이터 구조 먼저**: Excel 생성 전에 완전한 데이터 구조 준비
- [OK] **전체 컬럼 채우기**: **20개 컬럼 모두** 값 존재 (13-20번은 기본값으로 자동 채우기)
- [OK] **셀 병합 알고리즘**: apply_cell_merge 함수 적용 (A-E 컬럼만)
- [OK] **행 높이 설정**: 데이터 행(Row 7+) 높이 100 설정 (텍스트 잘림 방지)
- [OK] **최종 검증**: verify_excel 함수로 생성 후 검증
- [OK] **WebSearch 기반 항목 생성 (품질 우선, 개수 제한 없음)**: 의미있는 항목이면 개수 제한 없음, 억지로 개수 맞추기 금지
- [OK] **제품 라이프사이클 4단계** 반영 (DFMEA/PFMEA 모두 1-4단계, 개선 초점이 다름)
- [OK] **품질 체크리스트** 통과

---

## 이전 문제 해결 매핑

| 이전 문제 | 해결 방법 |
|----------|----------|
| [X] 매번 다른 결과 | [OK] sort_fmea_data 함수로 고정된 정렬 순서 + **엄격한 형식 규칙** |
| [X] **동일 고장영향이 분리됨** | [OK] **정렬 키에 기능+고장영향 포함! 부품명→기능→고장영향→S 순** |
| [X] **다이아몬드 구조 병합 불가** | [OK] **정렬 순서와 병합 계층 일치 + validate_merge_contiguity() 검증** |
| [X] 셀 병합 오류 | [OK] 명확한 병합 알고리즘 (parent 조건 포함) + **데이터 정렬 필수** |
| [X] 병합이 간헐적으로 안됨 | [OK] Excel 생성 전 sort_fmea_data 함수 **반드시** 실행 |
| [X] 빈 셀 발생 (1-12번) | [OK] validate_data 검증으로 빈 값 방지 |
| [X] 빈 셀 발생 (13-20번) | [OK] fill_default_values로 기본값 자동 채우기 |
| [X] **텍스트 잘림 (고장메커니즘 등)** | [OK] **행 높이 100 설정 (wrap_text만으로는 부족)** |
| [X] **표기 형식이 매번 다름** | [OK] **엄격한 형식 규칙 + validate_data 형식 검증** |
| [X] **"고장영향 1:" 같은 번호 붙음** | [OK] **번호 표기 패턴 검출 및 오류 발생** |

---

## 직접 openpyxl 코딩 시 완전한 예제

**[!] 클로드 웹 환경 전용**: Python 스크립트 실행이 불가능한 경우에만 사용

### 필수 구현 체크리스트

- [ ] 1. 데이터 정렬 (sort_fmea_data)
- [ ] 2. 데이터 검증 (validate_data)
- [ ] 3. Excel 생성 (Row 1-6 헤더 + Row 7+ 데이터)
- [ ] 4. 셀 병합 (A-E 컬럼, **parent 조건 필수**)
- [ ] 5. 서식 적용 (폰트, 색상, 정렬, 테두리)

### 핵심 코드: 셀 병합 알고리즘 (parent 조건)

```python
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

def apply_cell_merge_with_parent(ws, data, start_row=7):
    """셀 병합 (A-E 컬럼, parent 조건 적용)

    CRITICAL: 고장영향(C)이 바뀌면 고장형태(E)도 구분되어야 함!
    """

    # 병합 규칙: (컬럼, 키, parent 키)
    merge_rules = [
        ('A', '부품명', None),           # 부품명: parent 없음
        ('B', '기능', '부품명'),          # 기능: 같은 부품 내에서만
        ('C', '고장영향', '기능'),        # 고장영향: 같은 기능 내에서만
        ('D', 'S', '고장영향'),           # S: 같은 고장영향 내에서만
        ('E', '고장형태', '고장영향')     # 고장형태: 같은 고장영향 내에서만 (CRITICAL!)
    ]

    for col_letter, col_name, parent_col in merge_rules:
        i = 0
        while i < len(data):
            merge_start = start_row + i
            current_value = data[i][col_name]

            # parent 조건 확인
            parent_value = None
            if parent_col:
                parent_value = data[i][parent_col]

            # 연속된 같은 값 찾기
            j = i + 1
            while j < len(data):
                # 값이 같은지 확인
                if data[j][col_name] == current_value:
                    # parent가 있으면 parent도 같아야 병합
                    if parent_col is None or data[j][parent_col] == parent_value:
                        j += 1
                    else:
                        # parent가 다르면 병합 중단 (예: 고장영향이 바뀜)
                        break
                else:
                    # 값이 다르면 병합 중단
                    break

            # 2개 이상 행이면 병합
            merge_end = start_row + j - 1
            if merge_end > merge_start:
                ws.merge_cells(f'{col_letter}{merge_start}:{col_letter}{merge_end}')
                ws[f'{col_letter}{merge_start}'].alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

            i = j  # 다음 구간으로 이동

# 예시 사용
# fmea_data = [정렬된 FMEA 데이터 리스트]
# wb = Workbook()
# ws = wb.active
# ... (헤더 및 데이터 작성)
# apply_cell_merge_with_parent(ws, fmea_data, start_row=7)
# wb.save('output.xlsx')
```

### 올바른 병합 예시

**규소강판 데이터**:
```python
[
  {'부품명': '규소강판', '기능': '기계적 지지', '고장영향': '변형', 'S': 7, '고장형태': '크랙', ...},     # Row 7
  {'부품명': '규소강판', '기능': '기계적 지지', '고장영향': '변형', 'S': 7, '고장형태': '크랙', ...},     # Row 8
  {'부품명': '규소강판', '기능': '기계적 지지', '고장영향': '진동 소음', 'S': 5, '고장형태': '이완', ...}, # Row 9
  {'부품명': '규소강판', '기능': '기계적 지지', '고장영향': '진동 소음', 'S': 5, '고장형태': '이완', ...}, # Row 10
  {'부품명': '규소강판', '기능': '부식 방지', '고장영향': '재료 열화', 'S': 6, '고장형태': '부식', ...},   # Row 11
  ...
]
```

**올바른 E컬럼(고장형태) 병합**:
- E7:E8 (고장영향 "변형" + 고장형태 "크랙")
- E9:E10 (고장영향 "진동 소음" + 고장형태 "이완")
- E11:E15 (고장영향 "재료 열화" + 고장형태 "부식")

**[X] 잘못된 병합** (parent 조건 무시):
- E7:E14 (고장형태만 보고 전체 병합) ← 규소강판_FMEA_8.xlsx 문제!

### 전체 워크플로우 예제

```python
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

# 1. 데이터 정렬 (반드시 필요!)
# [!] 정렬 순서: 부품명 → S(내림차순) → 고장영향 → 고장형태 → 고장원인
fmea_data_sorted = sort_fmea_data(fmea_data)  # scripts/generate_fmea_excel.py 참조

# 2. 검증
validate_data(fmea_data_sorted)
validate_logical_consistency(fmea_data_sorted)

# 3. Excel 생성
wb = Workbook()
ws = wb.active
ws.title = "FMEA"

# 4. 헤더 작성 (Row 1-6)
ws.merge_cells('A1:T1')
ws['A1'] = "{부품명}_FMEA"
ws['A1'].font = Font(bold=True, size=16)
ws['A1'].alignment = Alignment(horizontal='center', vertical='center')

# Row 2: 프로젝트
ws.merge_cells('A2:T2')
ws['A2'] = "프로젝트: 초고압 변압기"

# Row 3: 자료 출처
ws.merge_cells('A3:T3')
ws['A3'] = "자료 출처: IEC 60076-1, CIGRE TB 642, Claude 전문 지식"

# Row 6: 컬럼 헤더
headers = ['부품명', '기능', '고장영향', 'S', '고장형태', '고장원인', '고장메커니즘',
           '현재예방대책', 'O', '현재검출대책', 'D', 'AP',
           '예방조치', '검출조치', '담당자', '목표일', "S'", "O'", "D'", "AP'"]
for col_idx, header in enumerate(headers, start=1):
    cell = ws.cell(row=6, column=col_idx, value=header)
    cell.font = Font(bold=True, color='FFFFFF')
    cell.fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    cell.alignment = Alignment(horizontal='center', vertical='center')

# 5. 데이터 작성 (Row 7+)
for row_idx, item in enumerate(fmea_data_sorted, start=7):
    ws.cell(row=row_idx, column=1, value=item['부품명'])
    ws.cell(row=row_idx, column=2, value=item['기능'])
    ws.cell(row=row_idx, column=3, value=item['고장영향'])
    ws.cell(row=row_idx, column=4, value=item['S'])
    ws.cell(row=row_idx, column=5, value=item['고장형태'])
    ws.cell(row=row_idx, column=6, value=item['고장원인'])
    # ... (나머지 컬럼)

# 6. 셀 병합 (CRITICAL!)
apply_cell_merge_with_parent(ws, fmea_data_sorted, start_row=7)

# 7. AP 컬럼 색상 적용 (AIAG-VDA 2019 표준)
ap_colors = {
    'H': PatternFill(start_color='C00000', end_color='C00000', fill_type='solid'),  # 빨강
    'M': PatternFill(start_color='FFC000', end_color='FFC000', fill_type='solid'),  # 노랑
    'L': PatternFill(start_color='92D050', end_color='92D050', fill_type='solid')   # 녹색
}
for row_idx, item in enumerate(fmea_data_sorted, start=7):
    # AP (L열)
    ap_value = item.get('AP', 'L')
    if ap_value in ap_colors:
        ws[f'L{row_idx}'].fill = ap_colors[ap_value]
        ws[f'L{row_idx}'].font = Font(bold=True, color='FFFFFF')

    # AP' (T열)
    ap_prime = item.get("AP'", 'L')
    if ap_prime in ap_colors:
        ws[f'T{row_idx}'].fill = ap_colors[ap_prime]
        ws[f'T{row_idx}'].font = Font(bold=True, color='FFFFFF')

# 8. 행 높이 설정 (데이터 행)
for row_idx in range(7, len(fmea_data_sorted) + 7):
    ws.row_dimensions[row_idx].height = 100  # 충분한 높이 (텍스트 잘림 방지)

# 9. 틀고정 (Row 1-6 고정, Row 7부터 스크롤)
ws.freeze_panes = 'A7'

# 10. 저장
wb.save('output.xlsx')
print("[OK] Excel 생성 완료")
```

**[!] 주의**: 이 방법은 클로드 웹 환경 전용입니다. Claude Code에서는 반드시 `python scripts/generate_fmea_excel.py` 사용!
