# FMEA 검증 가이드라인 (CRITICAL!)

## 왜 이 가이드라인이 필요한가?

**실제 규소강판_FMEA_5.xlsx 분석 결과** (2025-11-22):
- 총 83개 항목 중 **56건 (67.5%)이 Failure Chain 위반**
- 고장영향 → 고장원인 직접 연결 (중간 고장형태 누락)
- 고장메커니즘이 물리적 과정 없이 현상만 나열
- 현재예방대책이 일반적 표현만 사용 (구체적 정보 없음)
- S/O 값이 WebSearch 근거 없이 일괄 높은 점수 부여

**AIAG-VDA 2019 핵심 원칙**:
> "Each failure mode, cause and effect relationship must be assessed."
> — AIAG-VDA FMEA Handbook, Section 3.4

이 가이드는 **FMEA TFT 팀원들이 Claude 스킬로 생성한 Excel을 바로 실무에 활용**할 수 있도록 품질을 보장합니다.

---

## 0. [!!] 기능-고장영향 인과관계 검증 (최최우선!)

### 왜 이 검증이 가장 먼저인가?

**기존 검증의 한계**: Failure Chain 검증은 "고장형태 → 고장원인" 연결만 확인했음.
**누락된 검증**: "기능 → 고장영향" 연결의 논리성은 검증하지 않았음!

```text
기능 → 고장영향 → 고장형태 → 고장원인
  ↑        ↑           ↑          ↑
 0순위    1순위       2순위      3순위
(신규!)  (기존)      (기존)     (기존)
```

### 검증 규칙

**규칙 0 (신규!)**: 기능 실패 시 해당 고장영향이 실제로 발생하는가?

```python
def validate_function_effect_causality(function: str, effect: str) -> dict:
    """기능-고장영향 인과관계 검증 (CRITICAL!)

    Args:
        function: 기능 (예: "손실을 최소화한다")
        effect: 고장영향 (예: "효율 저하")

    Returns:
        {"valid": bool, "reason": str, "suggestion": str}
    """

    # 기능에서 동사 추출
    verb_mapping = {
        "최소화": {"allowed": ["증가", "상승", "초과", "저하"],
                  "forbidden": ["소음", "외관", "접지", "누유"]},
        "전달": {"allowed": ["불가", "불량", "저하", "차단"],
                "forbidden": ["외관", "접지", "누유", "소음"]},
        "고정": {"allowed": ["이완", "이동", "변위", "탈락", "진동"],
                "forbidden": ["효율", "손실", "절연", "과열"]},
        "절연": {"allowed": ["파괴", "단락", "누전", "지락", "열화"],
                "forbidden": ["진동", "소음", "외관", "이완"]},
        "지지": {"allowed": ["변형", "좌굴", "붕괴", "처짐", "파손"],
                "forbidden": ["효율", "손실", "절연", "과열"]},
        "냉각": {"allowed": ["과열", "온도상승", "열화", "소손"],
                "forbidden": ["외관", "소음", "접지", "이완"]},
        "밀봉": {"allowed": ["누유", "누기", "침수", "오염"],
                "forbidden": ["효율", "진동", "소음", "과열"]},
        "접지": {"allowed": ["다점접지", "접지불량", "순환전류", "감전"],
                "forbidden": ["외관", "효율", "진동", "소음"]},
        "억제": {"allowed": ["증가", "과다", "초과", "상승"],
                "forbidden": ["효율", "접지", "절연"]},
        "제공": {"allowed": ["부족", "불가", "차단", "저하"],
                "forbidden": ["외관", "소음"]}
    }

    # 기능에서 동사 추출
    detected_verb = None
    for verb in verb_mapping.keys():
        if verb in function:
            detected_verb = verb
            break

    if not detected_verb:
        return {
            "valid": False,
            "reason": f"기능 '{function}'에서 동사를 식별할 수 없음",
            "suggestion": "기능을 '[목적어]를 [동사]한다' 형식으로 재작성"
        }

    rules = verb_mapping[detected_verb]

    # 허용 키워드 확인
    effect_allowed = any(kw in effect for kw in rules["allowed"])

    # 금지 키워드 확인
    effect_forbidden = any(kw in effect for kw in rules["forbidden"])

    if effect_forbidden:
        return {
            "valid": False,
            "reason": f"'{function}' 실패 시 '{effect}'는 발생하지 않음 (인과관계 없음)",
            "suggestion": f"이 고장영향에 맞는 새 기능 추가 필요 (예: '진동을 억제한다')"
        }

    if not effect_allowed:
        return {
            "valid": False,
            "reason": f"'{function}' 실패와 '{effect}'의 인과관계 불명확",
            "suggestion": f"허용 키워드: {rules['allowed']}"
        }

    return {
        "valid": True,
        "reason": f"'{detected_verb}' 실패 → '{effect}' 논리적으로 타당",
        "suggestion": None
    }
```

### 전체 DataFrame 검증

```python
def validate_all_function_effect_causality(df) -> list:
    """전체 FMEA의 기능-고장영향 인과관계 검증"""
    errors = []

    for idx, row in df.iterrows():
        function = row.get('기능', '')
        effect = row.get('고장영향', '')

        if pd.isna(function) or pd.isna(effect):
            continue

        result = validate_function_effect_causality(function, effect)

        if not result["valid"]:
            errors.append({
                "row": idx + 7,  # Excel 행 번호 (헤더 고려)
                "function": function,
                "effect": effect,
                "reason": result["reason"],
                "suggestion": result["suggestion"]
            })

    if errors:
        print(f"[X] 기능-고장영향 인과관계 오류: {len(errors)}건")
        for err in errors[:5]:  # 상위 5개만 출력
            print(f"  Row {err['row']}: '{err['function']}' → '{err['effect']}'")
            print(f"    문제: {err['reason']}")
            print(f"    해결: {err['suggestion']}")
        if len(errors) > 5:
            print(f"  ... 외 {len(errors) - 5}건")
    else:
        print("[OK] 기능-고장영향 인과관계 검증 통과")

    return errors
```

### 검증 예시

```text
[X] 잘못된 연결:
  기능: "손실을 최소화한다" → 고장영향: "소음 기준 초과"
  문제: '최소화' 실패 시 '소음'은 발생하지 않음 (인과관계 없음)
  해결: 새 기능 "진동을 억제한다" 추가 필요

[OK] 올바른 연결:
  기능: "손실을 최소화한다" → 고장영향: "효율 저하"
  이유: '최소화' 실패 → '저하' 논리적으로 타당
```

---

## 1. Failure Chain 검증 프로세스 (최우선!)

### AIAG-VDA Failure Chain 구조

```
기능 (Function)
  └─ 고장영향 (Effect)           ← 기능 상실로 인한 결과
      └─ 고장형태 (Mode)          ← 영향을 일으키는 고장 형태
          └─ 고장원인 (Cause)      ← 모드를 발생시키는 근본 원인
              └─ 고장메커니즘      ← 원인의 물리적 과정
```

### 필수 검증 규칙

**규칙 1**: 모든 고장원인은 고장형태를 가져야 함
- [X] 고장영향 "변압 불가" → 고장원인 "설계: 단면적 부족"
- [OK] 고장영향 "변압 불가" → 고장형태 "부족" → 고장원인 "설계: 단면적 부족"

**규칙 2**: 모든 고장형태는 고장영향을 가져야 함
- [X] 고장형태 "과도" → 고장원인 "재료: 전기 저항 부족"
- [OK] 고장영향 "철손 증가" → 고장형태 "과도" → 고장원인 "재료: 전기 저항 부족"

**규칙 3**: 1개 고장영향 → N개 고장형태 (WebSearch에서 발견된 고장 형태)
- 억지로 개수를 맞추지 않음
- WebSearch에서 발견된 실제 고장형태만 사용

**규칙 4**: 1개 고장형태 → N개 고장원인 (WebSearch에서 발견된 근본 원인)
- 억지로 개수를 맞추지 않음
- WebSearch에서 발견된 실제 원인만 사용

### 생성 중 실시간 검증

**Step 1: 피라미드 구조 계획**

```
예시: 기능 "자속 전달"

1. 고장영향 2개 선택:
   - "변압 불가"
   - "전압 변환 불량"

2. 각 영향별 고장형태 3개 선택 (구체적 현상):
   영향 "변압 불가":
     - 모드 "층간단락" (자속 경로 완전 차단)
     - 모드 "절연파괴" (절연 손상으로 단락)
     - 모드 "열화" (경년 열화로 성능 감소)

   영향 "전압 변환 불량":
     - 모드 "접촉불량" (부하 변동 시 일시 저하)
     - 모드 "변형" (자속 경로 이탈)
     - 모드 "과열" (과포화로 비선형 특성)

3. 각 모드별 고장원인 3개 생성:
   모드 "층간단락" → 원인 3개 (설계, 재료, 제작)
   모드 "절연파괴" → 원인 3개
   ...

총: 2개 영향 × 3개 모드 × 3개 원인 = 18개 항목
```

**Step 2: 항목 생성 시 체크**

```python
# 의사 코드 (Pseudo Code)
for each 고장원인:
    if 고장형태 == None:
        ERROR: "고장원인이 고장형태 없이 고장영향과 직접 연결됨!"
        → 해당 원인의 고장형태를 구체적 현상으로 선택

    if 고장영향 == None:
        ERROR: "고장형태가 고장영향 없이 독립적으로 존재함!"
        → 해당 모드의 고장영향을 선택
```

**Step 3: Excel 생성 전 최종 검증**

```python
def validate_failure_chain(df):
    """Failure Chain 완전성 검증"""
    errors = []

    # 검증 1: 고장원인 → 고장형태 연결
    for idx, row in df.iterrows():
        if pd.notna(row['고장원인']) and pd.isna(row['고장형태']):
            errors.append(f"Row {idx+7}: 고장원인 '{row['고장원인']}' 있으나 고장형태 누락!")

    # 검증 2: 고장형태 → 고장영향 연결
    for idx, row in df.iterrows():
        if pd.notna(row['고장형태']) and pd.isna(row['고장영향']):
            errors.append(f"Row {idx+7}: 고장형태 '{row['고장형태']}' 있으나 고장영향 누락!")

    # 검증 3: Failure Chain 논리적 연결 확인
    # (개수 강제 아님 - WebSearch 기반 자연스러운 연결만 확인)

    if errors:
        raise ValueError("\n".join(errors))

    return "[OK] Failure Chain 검증 통과"
```

### 피라미드 구조 시각화 (필수!)

**생성 과정 예시**:

```
Step 1: 기능 "자속 유도" 선택

Step 2: 고장영향 "무부하 손실 증가" 생성

Step 3: 고장형태 3개 선택
  ├─ "과도" (와전류 과다)
  ├─ "저하" (경년 열화)
  └─ "역효과" (개선 시도의 역효과)

Step 4: 각 모드당 원인 3개 생성
  "과도":
    ├─ 설계: 자속 밀도 과설계
    ├─ 재료: 전기 저항 부족
    └─ 제작: 층간 절연 손상

  "저하":
    ├─ 재료: 절연 코팅 경년 열화
    ├─ 제작: 압착력 과다로 코팅 파괴
    └─ 시험: 절연 저항 시험 누락

  "역효과":
    ├─ 설계: 과도한 적층 매수로 조립 손상
    ├─ 제작: 냉각 불균형으로 열응력
    └─ 시험: 온도 상승 시험 미실시

총: 1개 영향 × 3개 모드 × 3개 원인 = 9개 항목
```

**[X] 절대 금지**: 고장영향 → 고장원인 직접 연결

```
[X] 잘못된 구조:
  고장영향 "변압 불가"
    └─ 고장원인 "설계: 단면적 부족"  ← 고장형태 누락!

[OK] 올바른 구조:
  고장영향 "변압 불가"
    └─ 고장형태 "부족"
        └─ 고장원인 "설계: 단면적 부족"
```

---

## 2. 고장메커니즘 구체성 기준

### 정의

**고장메커니즘**: 고장원인이 고장형태로 발전하는 **물리적 과정**

### 핵심 요구사항

- **논리적 연결**: 원인 → 물리적 변화 → 고장형태 연결
- **물리적 원리**: 전자기력, 열, 응력, 화학 반응 등 명시
- **WebSearch 기반**: 실제 문헌에서 확인된 메커니즘 사용

### [X] 잘못된 메커니즘 (현상만 나열)

**문제점**: 물리적 과정 없이 결과만 나열

```
1. "항복 강도 미달" (8자)
   → 왜 미달? 어떤 물리적 과정?

2. "체결 토크 부족" (7자)
   → 메커니즘이 아닌 현상

3. "재료 시험 미실시" (8자)
   → 시험 누락은 메커니즘 아님

4. "전압 상승" (5자)
   → 극도로 짧음, 물리적 과정 없음

5. "절연 코팅 손상" (7자)
   → 어떻게 손상? 물리적 메커니즘?
```

### [OK] 올바른 메커니즘 (물리적 과정)

**특징**: 원인 → 물리적 변화 → 결과 명확

```
1. "단락 전자력이 항복 강도를 초과하여 적층 변형 발생" (27자)
   물리적 과정: 전자기력 > 기계적 강도 → 변형

2. "체결력 불균형으로 국부 갭 발생, 자속 집중 및 과열" (28자)
   물리적 과정: 불균형 체결 → 갭 → 자속 집중 → 열

3. "인장 시험 누락으로 저강도 재료 혼입, 단락 시 변형" (28자)
   물리적 과정: 시험 미실시 → 불량 재료 → 강도 부족 → 변형

4. "층간 절연 파괴로 와전류 경로 형성, 국부 과열 발생" (28자)
   물리적 과정: 절연 파괴 → 와전류 → 열

5. "온도 순환 반복으로 절연 코팅 균열, 절연 저항 저하" (28자)
   물리적 과정: 열 순환 → 균열 → 저항 저하
```

### 검증 체크리스트

- [ ] **물리적 원리 포함** (전자기력, 열, 응력, 화학 반응 등)
- [ ] **인과관계 명확** (원인 → 변화 → 결과)
- [ ] **WebSearch 기반** (실제 문헌에서 확인된 메커니즘)
- [ ] **메커니즘 vs 현상 구분** (과정 설명 vs 결과만)

### 검증 함수

```python
def validate_mechanism_specificity(text, min_length=15):
    """고장메커니즘 구체성 검증"""
    if pd.isna(text) or len(str(text)) == 0:
        return "ERROR: 고장메커니즘 누락"

    text = str(text)

    if len(text) < min_length:
        return f"WARNING: 메커니즘이 너무 짧음 ({len(text)}자 < {min_length}자)"

    # 현상만 나열한 경우 (물리적 과정 없음)
    generic_keywords = ['미달', '부족', '과다', '손상', '불량', '미실시', '상승', '저하']
    if any(kw in text for kw in generic_keywords) and len(text) < 20:
        return f"WARNING: 현상만 나열, 물리적 과정 추가 필요 ({text})"

    return "OK"

# 전체 DataFrame 검증
def validate_all_mechanisms(df):
    """전체 고장메커니즘 구체성 검증"""
    warnings = []
    for idx, row in df.iterrows():
        result = validate_mechanism_specificity(row['고장메커니즘'])
        if result != "OK":
            warnings.append(f"Row {idx+7}: {result}")

    if warnings:
        print("\n".join(warnings))
        print(f"\n총 {len(warnings)}건 개선 필요")
    else:
        print("[OK] 모든 고장메커니즘 구체성 통과")
```

---

## 3. 현재대책/조치 구체성 기준

### 핵심 요구사항

- **구체성**: 문서명, 기준값, 방법 포함
- **실행 가능성**: 실무에서 바로 찾아볼 수 있는 수준
- **WebSearch 기반**: 실제 표준/문헌에서 확인된 대책 사용

### [X] 일반적 표현 금지

**문제점**: 구체적 정보 없이 추상적 표현만

```
1. "구조 설계 기준" (7자)
   → 어떤 기준? 문서명? 기준값?

2. "재료 규격" (4자)
   → 어떤 규격? 표준 번호?

3. "조립 절차서" (5자)
   → 어떤 절차? 주요 내용?

4. "품질 강화" (5자)
   → 어떻게 강화? 구체적 방법?

5. "검사 실시" (5자)
   → 어떤 검사? 기준?
```

### [OK] 구체적 표현

**특징**: 문서명, 표준 번호, 기준값 명시

```
1. "기계적 강도 계산 기준 (IEC 60076-1, 단락 전자력 고려)" (32자)
   구체성: 표준 번호, 계산 대상 명시

2. "재료 인장 시방서 (항복 강도 ≥ 350 MPa)" (26자)
   구체성: 기준값 명시

3. "토크 관리 절차서 (체결 순서, 토크 값 XX Nm)" (27자)
   구체성: 관리 항목, 기준값 명시

4. "품질 검증 체크리스트 (치수, 외관, 절연 저항)" (26자)
   구체성: 검증 항목 명시

5. "인장 시험 (IEC 60404-8-6, 샘플링 10%)" (26자)
   구체성: 표준, 샘플링 비율 명시
```

### 일반적 표현 대체 가이드

| 일반적 표현 | 구체적 표현 예시 |
|------------|-----------------|
| "강화" | "품질 검증 체크리스트 추가 (치수, 외관, 절연)" |
| "개선" | "조립 토크 값 상향 (XX Nm → YY Nm)" |
| "확인" | "육안 검사 + 치수 측정 (±0.1mm 허용)" |
| "실시" | "인장 시험 (IEC 60404-8-6, 샘플링 10%)" |
| "관리" | "온도 관리 절차서 (측정 주기, 허용 범위)" |
| "검토" | "설계 검토 회의 (구조팀, 전기팀, 월 1회)" |

### 검증 함수

```python
def validate_measure_specificity(text, min_length=10):
    """대책 구체성 검증"""
    if pd.isna(text) or len(str(text)) == 0:
        return "ERROR: 대책 누락"

    text = str(text)

    if len(text) < min_length:
        return f"WARNING: 대책이 너무 짧음 ({len(text)}자 < {min_length}자)"

    # 일반적 표현 (구체성 부족)
    generic_keywords = ['강화', '개선', '확인', '실시', '관리', '검토', '기준', '규격', '절차서']
    if any(kw in text for kw in generic_keywords) and len(text) < 15:
        return f"WARNING: 일반적 표현 사용, 구체화 필요 ({text})"

    return "OK"

# 전체 DataFrame 검증
def validate_all_measures(df):
    """전체 대책 구체성 검증"""
    columns = ['현재예방대책', '현재검출대책', '예방조치', '검출조치']

    for col in columns:
        print(f"\n=== {col} 검증 ===")
        warnings = []
        for idx, row in df.iterrows():
            result = validate_measure_specificity(row[col])
            if result != "OK":
                warnings.append(f"Row {idx+7}: {result}")

        if warnings:
            print("\n".join(warnings[:10]))  # 상위 10개만 출력
            print(f"총 {len(warnings)}건 개선 필요")
        else:
            print("[OK] 모든 항목 구체성 통과")
```

---

## 4. 점수 합리성 검증

### 합리적 분포 기준

**핵심 원칙**:
- **S (심각도)**: WebSearch 기반 실제 영향도에 따라 결정
- **O (발생도)**: WebSearch 통계 (CIGRE/IEEE) 기반 결정
- **D (검출도)**: 실제 검출 방법/장비 기준 결정
- **강제 평균값 없음**: WebSearch 근거에 따라 자연스럽게 분포

### [X] 점수 인플레이션 (과대평가)

**실제 사례** (규소강판_FMEA_5.xlsx):
```
S: 범위 6-10 (최소값 6) ← 낮은 심각도 항목 없음
O: 범위 5-9 (최소값 5)  ← 낮은 발생도 항목 없음
D: 범위 2-6 (평균 4.0)  [OK] 양호
RPN: 평균 200.7         [!] 높음 (권장 ≤200)
```

**문제점**:
- S 최소값 6: 모든 고장이 심각 → 비현실적
- O 최소값 5: 모든 고장이 자주 발생 → 비현실적
- RPN 평균 200 초과: 전반적 과대평가

### [OK] 합리적 점수 분포

```
S: 범위 2-10 (최소 2, 평균 6.5) [OK]
  - S=2: 미미한 영향 (성능 1-2% 저하)
  - S=5: 중간 영향 (성능 10% 저하)
  - S=9: 심각한 영향 (기능 상실)

O: 범위 1-9 (최소 1, 평균 5.0) [OK]
  - O=1: 극히 드묾 (10년 1회)
  - O=4: 가끔 발생 (1년 1회)
  - O=8: 자주 발생 (1개월 1회)

D: 범위 1-8 (최소 1, 평균 4.0) [OK]
  - D=1: 확실히 검출 (100% 검출)
  - D=4: 보통 검출 (80% 검출)
  - D=8: 거의 불검출 (20% 검출)

RPN: 평균 150, 최대 480 [OK]
```

### 경고 조건

```python
def validate_scoring_distribution(df):
    """점수 분포 합리성 검증"""
    warnings = []

    # S (심각도) 검증
    s_min, s_mean = df['S'].min(), df['S'].mean()
    if s_min > 5:
        warnings.append(f"[!] S 최소값 {s_min} (권장 ≤5): 심각도 인플레이션 의심")
    if s_mean > 7.5:
        warnings.append(f"[!] S 평균 {s_mean:.1f} (권장 5-7): 전반적 과대평가")

    # O (발생도) 검증
    o_min, o_mean = df['O'].min(), df['O'].mean()
    if o_min > 4:
        warnings.append(f"[!] O 최소값 {o_min} (권장 ≤4): 발생도 과대평가 의심")
    if o_mean > 6.5:
        warnings.append(f"[!] O 평균 {o_mean:.1f} (권장 4-6): 전반적 과대평가")

    # D (검출도) 검증
    d_min, d_mean = df['D'].min(), df['D'].mean()
    if d_min > 5:
        warnings.append(f"[!] D 최소값 {d_min} (권장 ≤5): 검출 능력 과소평가")

    # RPN 검증
    df['RPN'] = df['S'] * df['O'] * df['D']
    rpn_avg, rpn_max = df['RPN'].mean(), df['RPN'].max()
    if rpn_avg > 200:
        warnings.append(f"[!] RPN 평균 {rpn_avg:.0f} (권장 ≤200): 전반적 위험도 과대평가")
    if rpn_max > 600:
        warnings.append(f"[!] RPN 최대값 {rpn_max} (권장 ≤600): 극단적 고위험 항목 검토 필요")

    # 개선 후 검증
    df['RPN_after'] = df["S'"] * df["O'"] * df["D'"]
    reduction = (df['RPN'].mean() - df['RPN_after'].mean()) / df['RPN'].mean() * 100
    if reduction < 30:
        warnings.append(f"[!] RPN 감소율 {reduction:.1f}% (권장 ≥30%): 개선 조치 효과 부족")

    if warnings:
        print("\n".join(warnings))
    else:
        print("[OK] 점수 분포 합리성 통과")

    return warnings
```

---

## 5. 담당자/목표일 현실성 가이드

### 담당자 분산 목표

**합리적 분포**:
- 최다 부서 ≤ 40% (한 부서 과다 방지)
- 라이프사이클 단계별 적절한 부서 할당

**라이프사이클 단계별 담당 부서**:
```
설계 단계 → 설계팀 (구조설계팀, 전기설계팀)
재료 단계 → 자재팀, 구매팀
제작 단계 → 생산팀, 제조팀
시험 단계 → 품질보증팀, 시험팀
```

**[X] 잘못된 분포** (규소강판_FMEA_5.xlsx):
```
품질보증팀: 32건 (38.6%) ← 거의 40%, 과다
생산팀: 24건 (28.9%) [OK]
전기설계팀: 14건 (16.9%) [OK]
구조설계팀: 4건 (4.8%) ← 너무 적음
```

**[OK] 올바른 분포**:
```
품질보증팀: 22건 (26.5%) [OK]
생산팀: 24건 (28.9%) [OK]
전기설계팀: 18건 (21.7%) [OK]
구조설계팀: 12건 (14.5%) [OK]
자재팀: 7건 (8.4%) [OK]
```

### 목표일 설정 기준

**AP (Action Priority)와 목표일 매칭**:
```
AP = H (High, >100): "즉시" (1개월 이내)
AP = M (Medium, 50-100): "3개월"
AP = L (Low, <50): "6개월"
```

**합리적 분포**:
- "즉시": 20-30% (AP=H, RPN ≥ 250)
- "3개월": 40-50% (AP=M, RPN 100-250)
- "6개월": 20-30% (AP=L, RPN < 100)

**[X] 잘못된 분포** (규소강판_FMEA_5.xlsx):
```
즉시: 37건 (44.6%) [!] 너무 많음 (비현실적)
3개월: 34건 (41.0%) [OK]
6개월: 12건 (14.5%) [OK]
```

**[OK] 올바른 분포**:
```
즉시: 22건 (26.5%) [OK]
3개월: 40건 (48.2%) [OK]
6개월: 21건 (25.3%) [OK]
```

### 논리 일관성 검증

```python
def validate_assignment_logic(df):
    """담당자/목표일 논리 일관성 검증"""
    warnings = []

    # AP와 목표일 일치 검증
    for idx, row in df.iterrows():
        ap = row['AP']
        deadline = row['목표일']

        # 논리 오류 검출
        if ap == 'H' and deadline == '6개월':
            warnings.append(f"Row {idx+7}: AP=H인데 목표일 '6개월' (논리 오류)")
        elif ap == 'L' and deadline == '즉시':
            warnings.append(f"Row {idx+7}: AP=L인데 목표일 '즉시' (논리 오류)")

    # 담당자 분산 검증
    dept_counts = df['담당자'].value_counts()
    total = len(df)
    for dept, count in dept_counts.items():
        pct = count / total * 100
        if pct > 40:
            warnings.append(f"[!] {dept}: {count}건 ({pct:.1f}%) 과다 (권장 ≤40%)")

    # 목표일 분포 검증
    deadline_counts = df['목표일'].value_counts()
    immediate_pct = deadline_counts.get('즉시', 0) / total * 100
    if immediate_pct > 30:
        warnings.append(f"[!] '즉시' {immediate_pct:.1f}% 과다 (권장 ≤30%, 비현실적)")

    if warnings:
        print("\n".join(warnings))
    else:
        print("[OK] 담당자/목표일 논리 일관성 통과")

    return warnings
```

---

## 6. 라이프사이클 4단계 분류

### 핵심 원칙 (WebSearch 기반)

```
[!] 비율을 맞추기 위해 억지로 항목을 만들지 말 것!
- WebSearch에서 발견된 원인을 해당 단계로 자연스럽게 분류
- 특정 단계가 0개여도 실제로 해당 원인이 없으면 OK
```

### 생성 중 실시간 모니터링

```python
def monitor_lifecycle_balance(df):
    """라이프사이클 4단계 분류 확인"""
    lc_counts = df['라이프사이클_추출'].value_counts()
    total = len(df)

    print("\n=== 라이프사이클 4단계 분류 현황 ===")

    target_stages = ['설계', '재료', '제작', '시험']

    for stage in target_stages:
        count = lc_counts.get(stage, 0)
        pct = count / total * 100
        print(f"  {stage} 단계: {count}건 ({pct:.1f}%)")

    print("\n참고: 비율은 강제 기준이 아닙니다. WebSearch 결과에 따라 자연스럽게 분포합니다.")

    # DFMEA 범위 외 단계 경고
    invalid_stages = ['운영', '운송', '설치', '폐기']
    for stage in invalid_stages:
        if stage in lc_counts:
            count = lc_counts[stage]
            print(f"[X] DFMEA 범위 아님: {stage} {count}건 제거 필요")

    print()
```

### DFMEA 범위 (1-4단계만)

**[OK] DFMEA 포함** (설계/재료/제작/시험):
- 설계 단계: 설계 기준, 계산, 표준 적용
- 재료 단계: 재질, 자재, 입고 검사
- 제작 단계: 가공, 조립, 용접, 치수
- 시험 단계: 시험 누락, 측정, 판정, 검사

**[X] DFMEA 제외** (운영/운송/설치/폐기):
- 운영 단계: 유지보수, 부하 관리 (PFMEA 영역)
- 운송 단계: 포장, 운송 (PFMEA 영역)
- 설치 단계: 현장 설치 (PFMEA 영역)
- 폐기 단계: 수명 종료 (별도 분석)

---

## 7. 종합 검증 체크리스트

### Excel 생성 전 최종 검증

```python
def comprehensive_validation(df):
    """종합 검증 (모든 기준)"""
    print("=" * 50)
    print("FMEA 종합 검증 시작")
    print("=" * 50)

    all_passed = True

    # 1. Failure Chain
    print("\n[1/7] Failure Chain 검증...")
    try:
        validate_failure_chain(df)
    except ValueError as e:
        print(f"[X] {e}")
        all_passed = False

    # 2. 고장메커니즘 구체성
    print("\n[2/7] 고장메커니즘 구체성 검증...")
    validate_all_mechanisms(df)

    # 3. 현재대책/조치 구체성
    print("\n[3/7] 현재대책/조치 구체성 검증...")
    validate_all_measures(df)

    # 4. 점수 합리성
    print("\n[4/7] 점수 분포 합리성 검증...")
    warnings = validate_scoring_distribution(df)
    if len(warnings) > 3:
        all_passed = False

    # 5. 담당자/목표일 논리성
    print("\n[5/7] 담당자/목표일 논리 일관성 검증...")
    validate_assignment_logic(df)

    # 6. 라이프사이클 균형
    print("\n[6/7] 라이프사이클 4단계 균형 검증...")
    monitor_lifecycle_balance(df)

    # 7. 고장형태 다양화
    print("\n[7/7] 고장형태 다양화 검증...")
    mode_counts = df['고장형태'].value_counts()
    max_mode = mode_counts.max()
    if max_mode > len(df) * 0.15:
        print(f"[!] 특정 고장형태 과다 사용: {mode_counts.idxmax()} {max_mode}건 ({max_mode/len(df)*100:.1f}%)")
    else:
        print("[OK] 고장형태 분포 균형")

    print("\n" + "=" * 50)
    if all_passed:
        print("[OK] 모든 검증 통과 - Excel 생성 가능")
    else:
        print("[!] 일부 검증 실패 - 개선 후 재검증 권장")
    print("=" * 50)

    return all_passed
```

### 품질 점수 계산

```python
def calculate_quality_score(df):
    """FMEA 품질 점수 계산 (0-100점)"""
    score = 100

    # Failure Chain (30점)
    fc_violations = 0
    for idx, row in df.iterrows():
        if pd.notna(row['고장원인']) and pd.isna(row['고장형태']):
            fc_violations += 1
    fc_score = max(0, 30 - (fc_violations / len(df) * 100))

    # 구체성 (30점)
    mech_avg_len = df['고장메커니즘'].apply(lambda x: len(str(x))).mean()
    meas_avg_len = df['현재예방대책'].apply(lambda x: len(str(x))).mean()
    spec_score = min(30, (mech_avg_len / 15 * 15) + (meas_avg_len / 10 * 15))

    # 점수 합리성 (20점)
    s_min, o_min = df['S'].min(), df['O'].min()
    rpn_avg = (df['S'] * df['O'] * df['D']).mean()
    rating_score = 20
    if s_min > 5: rating_score -= 5
    if o_min > 4: rating_score -= 5
    if rpn_avg > 200: rating_score -= 10

    # 라이프사이클 균형 (20점)
    lc_counts = df['라이프사이클_추출'].value_counts()
    total = len(df)
    balance_score = 20
    for stage in ['설계', '재료', '제작', '시험']:
        pct = lc_counts.get(stage, 0) / total * 100
        if pct < 15 or pct > 35:
            balance_score -= 5

    total_score = fc_score + spec_score + rating_score + balance_score

    print(f"\n=== FMEA 품질 점수 ===")
    print(f"Failure Chain: {fc_score:.0f}/30")
    print(f"구체성: {spec_score:.0f}/30")
    print(f"점수 합리성: {rating_score:.0f}/20")
    print(f"라이프사이클 균형: {balance_score:.0f}/20")
    print(f"총점: {total_score:.0f}/100")

    if total_score >= 85:
        print("등급: A (실무 즉시 활용 가능)")
    elif total_score >= 70:
        print("등급: B (소폭 개선 후 활용 가능)")
    elif total_score >= 60:
        print("등급: C (중간 개선 후 활용 가능)")
    else:
        print("등급: D (중대한 개선 필요)")

    return total_score
```

---

## 활용 방법

### FMEA 생성 시

1. **항목 생성 중**: Failure Chain 피라미드 구조 준수
2. **메커니즘 작성 시**: 15자 이상, 물리적 과정 포함
3. **대책 작성 시**: 10자 이상, 문서명/기준값 명시
4. **점수 부여 시**: 1-10 전 범위 사용, 인플레이션 주의
5. **담당자 할당 시**: 라이프사이클 단계별 적절한 부서
6. **목표일 설정 시**: AP와 논리적 일관성 유지

### Excel 생성 후

```python
# 검증 실행
df = pd.read_excel("규소강판_FMEA.xlsx", skiprows=5)
comprehensive_validation(df)
quality_score = calculate_quality_score(df)

# 개선 필요 시
if quality_score < 85:
    print("\n개선 권장 사항:")
    # ... 개선 가이드 출력
```

---

## 참고 문헌

- AIAG & VDA FMEA Handbook (2019)
- IEC 60076 시리즈 (변압기 표준)
- IEEE C57 시리즈 (변압기 시험)
- CIGRE TB 642 (변압기 고장 분석)
