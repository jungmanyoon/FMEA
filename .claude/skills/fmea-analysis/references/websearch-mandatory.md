# WebSearch 필수 검증 가이드

**목적**: FMEA 작성 전 정확한 기술 정보 확보 (IEC/IEEE/CIGRE/Transformer Magazine)

---

## [!] 우선순위 명확화 (CRITICAL!)

> **WebSearch는 "보완용"! 내부 문서 분석이 먼저!**

### 자료 참조 순서 (필수 준수)

```
1순위: 내부 문서 (먼저 분석!)
  +-- 기능분석 다이어그램 (기능 정의 - BLOCKING!)
  +-- CHECK SHEET (고장형태, 예방대책)
  +-- 작업표준 W시리즈 (고장원인)
  +-- 검사기준 R/I/P시리즈 (검출대책)
  +-- 도시바TD 시리즈 (기술 사양, 설계 기준) [!] 중요!
  +-- QA DB (품질 이력, O값 근거)

2순위: WebSearch (내부 문서에 없는 정보만!)
  +-- IEC/IEEE/CIGRE/Transformer Magazine
```

### 내부 문서 분석 완료 후 WebSearch 실행 조건

- [ ] 기능분석 다이어그램에서 기능 정의 완료
- [ ] CHECK SHEET에서 고장형태/예방대책 후보 추출 완료
- [ ] W시리즈에서 고장원인 후보 추출 완료
- [ ] R/I/P시리즈에서 검출대책 후보 추출 완료
- [ ] TD시리즈에서 기술 사양/설계 기준 확인 완료
- [ ] **위 내부 문서에서 찾지 못한 정보만** WebSearch로 보완

**상세**: [qa-data-mapping.md](qa-data-mapping.md), [internal-docs-index.md](internal-docs-index.md)

---

## WebSearch 5개 출처 (보완용)

**WebSearch 사용 조건**: **내부 문서 분석 완료 후**, 부족한 정보만 검색

---

## 필수 WebSearch 5개 출처

### 1. IEC 표준 (국제전기기술위원회)

**검색어**: `"IEC 60076 {부품명} design requirements transformer"`

**목적**:
- 변압기 설계 요구사항 및 성능 기준
- 시험 절차 및 허용 한계 정의
- 절연, 온도, 기계적 강도 등 표준 규격

**활용**:
- 설계 기준: IEC 표준 설계 요구사항 참조
- S/O/D 기준: IEC 시험 기준 및 허용 한계
- 예방 대책: IEC 권장 설계 사항

**예시 (CORE)**:
```
WebSearch: "IEC 60076 core design requirements transformer"
결과:
- IEC 60076-1: Core flux density limits (정격 및 성능 기준)
- IEC 60076-5: Short-circuit withstand capability (단락 내전력)
- IEC 60404-8-4: Magnetic properties of electrical steel (전기강판 자기 특성)
```

---

### 2. IEEE 표준 (미국전기전자학회)

**검색어**:
- **주 검색어**: `"IEEE C57.125 {부품명} failure investigation transformer"`
- **보조 검색어**: `"IEEE C57.12 {부품명} transformer"`

**목적**:
- 고장 조사 및 분석 방법 (IEEE C57.125 - 고장 조사 전용 표준)
- 변압기 표준 및 시험 절차 (IEEE C57.12 시리즈)
- 고장 사례 및 통계
- 진단 기법

**활용**:
- 고장 원인: IEEE 분석 결과 참조
- 검출 대책: IEEE 권장 진단 방법
- O 값: IEEE 고장 빈도 데이터

**예시 (CORE)**:
```
WebSearch 1: "IEEE C57.125 core failure investigation transformer"
결과:
- IEEE C57.125: Core grounding fault analysis (고장 조사 전용)
- IEEE C57.125: Failure investigation procedures

WebSearch 2: "IEEE C57.12 core transformer"
결과:
- IEEE C57.12.00: General requirements (일반 요구사항)
- IEEE Std C57.104: Core diagnosis methods (진단 방법)
```

---

### 3. CIGRE 기술 브로슈어 (국제대전력시스템회의)

**검색어**: `"CIGRE {부품명} transformer failure statistics"`

**목적**:
- 실제 고장 통계 데이터
- 고장 패턴 및 트렌드
- 신뢰성 분석

**활용**:
- O 값: CIGRE 통계 데이터 기반
- S 값: 실제 고장 영향 사례
- 고장 형태 우선순위

**예시 (CORE)**:
```
WebSearch: "CIGRE core transformer failure statistics"
결과:
- CIGRE TB 642: Transformer reliability survey
- CIGRE TB 393: Core failure rate 0.05%/year
```

---

### 4. Transformer Magazine

**검색어**: `"Transformer Magazine {부품명} failure case study"`

**목적**:
- 실제 고장 사례
- 근본 원인 분석
- 교훈 및 대책

**활용**:
- 고장 메커니즘: 실제 사례 기반
- 고장 원인: 근본 원인 분석 결과
- 예방 대책: 사례에서 배운 교훈

**예시 (CORE)**:
```
WebSearch: "Transformer Magazine core failure case study"
결과:
- Case: 적층 절연 코팅 열화 → 와전류 손실 증가
- Root cause: 제작 시 적층 압착력 부족
- Lesson: 압착력 관리 기준 수립 필요
```

---

### 5. 일반 검색 (최신 사례)

**검색어**: `"{부품명} transformer common failures root cause"`

**목적**:
- 최신 고장 사례
- 실무 지식
- 업계 트렌드

**활용**:
- 최신 고장 형태
- 새로운 대책
- 실무 경험

---

## 검색 순서 (필수)

### Step 1: WebSearch 실행 (5개 모두)

```
1. IEC 60076 {부품명} design requirements transformer
2. IEEE C57.125 {부품명} failure investigation transformer (주), IEEE C57.12 {부품명} transformer (보조)
3. CIGRE {부품명} transformer failure statistics
4. Transformer Magazine {부품명} failure case study
5. {부품명} transformer common failures root cause
```

### Step 2: 검색 결과 분석 및 정리

**정리 항목**:
1. **실제 고장 형태 패턴** (IEC/IEEE 표준 용어)
2. **표준 정의 고장 원인** (IEC/IEEE/CIGRE)
3. **업계 표준 대책** (IEC/IEEE)
4. **과거 사례 기반 S/O/D** (CIGRE/Transformer Magazine)

**정리 형식**:
```
부품명: {부품명}

[고장 형태]
1. {IEC 표준 용어} - 출처: IEC 60076-X
2. {IEEE 표준 용어} - 출처: IEEE C57.XX
...

[고장 원인]
1. {원인} - 출처: CIGRE TB XXX
2. {원인} - 출처: Transformer Magazine Case Study
...

[예방 대책]
1. {대책} - 출처: IEC 60076-X
2. {대책} - 출처: IEEE C57.XXX
...

[검출 대책]
1. {대책} - 출처: IEEE C57.XXX
2. {대책} - 출처: IEC 60076-X
...
```

### Step 3: FMEA 항목 생성 시작

**검증 사항**:
- [OK] 5개 출처 모두 검색 완료
- [OK] 검색 결과 정리 완료
- [OK] 표준 용어 사용 준비
- [OK] 출처 명시 준비 (Excel Row 3에 실제 사용한 출처만)

**검증 실패 시**: FMEA 생성 중단, 검색 재실행

---

## 검색 결과 활용

### IEC 표준 → 설계 요구사항, 시험 기준

**예시**:
```
설계 기준: "자속 밀도 ≤1.7T (IEC 60076-1)"
현재 예방 대책: "단락 내전력 검증 (IEC 60076-5)"
현재 검출 대책: "절연 저항 시험 (IEC 60076-3)"
```

### IEEE 표준 → 고장 조사, 분석 방법

**예시**:
```
고장 원인: "철심 다점 접지 (IEEE C57.125 분석 방법)"
검출 대책: "접지 전류 측정 (IEEE C57.125 권장)"
```

### CIGRE → 통계 데이터, 고장 사례

**예시**:
```
O 값: 2 (CIGRE TB 642: 발생률 0.1%/year)
S 값: 8 (CIGRE 사례: 변압기 소손)
```

### Transformer Magazine → 실제 사례, 근본 원인

**예시**:
```
고장 원인: "설계: 적층 절연 코팅 두께 설계 오류"
고장 메커니즘: "절연 코팅 열화 → 층간 단락 → 와전류 증가"
(출처: Transformer Magazine 2023, Case Study)
```

---

## [*] 시점별 고장영향 검색 (추가 권장)

**목적**: 제작 중/시험 중 고장영향 누락 방지 (운전 중만 검색하면 예방 기회 상실!)

### 1. 제작 중 고장 검색

**검색어**:
```
WebSearch: "IEC 60076 {부품명} manufacturing defects quality control"
WebSearch: "transformer {부품명} manufacturing failure welding bonding"
WebSearch: "CIGRE {부품명} factory defect detection"
```

**목적**:
- 제작 과정 결함 패턴 파악
- 공장 내 검사 기준 확보
- 조기 발견 가능한 고장 형태 식별

**활용 (C열 고장영향 - 제작 중 발견, S=2-5)**:
> 주의: "조립 불합격", "용접 불량"은 발견 장소/고장형태이므로 고장영향 아님!
- 조립 정밀도 저하 (S=4)
- 재작업 필요 (S=3-4)
- 구조 변형 (S=5)
- 외관 품질 저하 (S=2-3)

### 2. 시험 중 고장 검색

**검색어**:
```
WebSearch: "IEEE C57.12 {부품명} factory acceptance test FAT failure"
WebSearch: "IEC 60076-1 {부품명} routine test type test failure"
WebSearch: "transformer {부품명} dielectric test insulation test failure"
```

**목적**:
- FAT 시험 불합격 패턴 파악
- 형식시험/루틴시험 기준 확보
- 출하 전 검출 가능한 고장 형태 식별

**활용 (C열 고장영향 - 시험 중 발견, S=4-7)**:
> 주의: "FAT 불합격", "내전압 시험 불합격"은 발견 장소이므로 고장영향 아님!
- 무부하 손실 초과 (S=6)
- 절연저항 저하 (S=5-6)
- 여자전류 증가 (S=5)
- PD(부분방전) 기준 초과 (S=6-7)
- 효율 저하 (S=6)

### 3. 운전 중 고장 검색 (기존 5개 출처에 포함)

**기존 검색으로 충분**: IEC/IEEE/CIGRE/Transformer Magazine 검색 결과에 운전 중 사례 다수 포함

**추가 검색 (필요 시)**:
```
WebSearch: "transformer {부품명} in-service failure field failure"
WebSearch: "CIGRE {부품명} operation phase failure statistics"
```

---

## 검증 체크리스트

### 검색 완료 확인

- [ ] IEC 표준 검색 완료
- [ ] IEEE 표준 검색 완료
- [ ] CIGRE 검색 완료
- [ ] Transformer Magazine 검색 완료
- [ ] 일반 검색 완료

### 검색 결과 정리 완료

- [ ] 고장 형태 목록 (표준 용어)
- [ ] 고장 원인 목록 (출처 명시)
- [ ] 예방 대책 목록 (출처 명시)
- [ ] 검출 대책 목록 (출처 명시)
- [ ] S/O/D 기준 데이터

### 품질 검증

- [ ] 표준/문헌 기반 고장 형태만 포함
- [ ] 비현실적 시나리오 제거
- [ ] 출처 명시 (Excel Row 3에 실제 사용한 출처만 준비)

### [*] 시점별 고장영향 검증

- [ ] 제작 중 고장영향 1개 이상 (S=2-5)
- [ ] 시험 중 고장영향 1개 이상 (S=4-7)
- [ ] 운전 중 고장영향 1개 이상 (S=7-10)
- [ ] 참조: [failure-effect-phases.md](failure-effect-phases.md)

---

## Excel Row 3 출처 명시 (MANDATORY)

**형식** (실제 사용한 출처만):
```
예시 1: 자료 출처: IEC 60076-1, IEC 60076-5, CIGRE TB 642, Claude 전문 지식
예시 2: 자료 출처: IEEE C57.12.00, Transformer Magazine, Claude 전문 지식
```

**[!] 주의**:
- **실제 WebSearch로 참조한 출처만 명시** (고정 템플릿 아님!)
- 검색하지 않은 출처는 제외
- Claude 전문 지식도 명시
- Excel Row 3에 반드시 기재

---

## 검색 실패 시 대응

### 검색 결과가 없는 경우

1. 검색어 변경
   - `"{부품명 영문} transformer failure"

`
   - `"{부품명 한글} 변압기 고장"`

2. 유사 부품 검색
   - 상위 시스템 검색 (예: 부싱 → 절연 시스템)

3. 표준 문서 직접 참조
   - IEC 60076 시리즈
   - IEEE C57 시리즈

4. Claude 전문 지식 활용
   - 표준 지식 기반 추론
   - 출처: "Claude 전문 지식" 명시

---

## 예시: CORE (철심) WebSearch 전체 과정

### 1. WebSearch 실행

```
Search 1: "IEC 60076 core design requirements transformer"
→ IEC 60076-1: Core flux density limits (자속 밀도 한계 ≤1.7T)
→ IEC 60076-5: Short-circuit withstand (단락 내전력 기준)
→ IEC 60404-8-4: Electrical steel properties (전기강판 특성)

Search 2-1: "IEEE C57.125 core failure investigation transformer"
→ IEEE C57.125: Core grounding fault investigation (접지 고장 조사)
→ IEEE C57.125: Multi-point grounding analysis (다점 접지 분석)

Search 2-2: "IEEE C57.12 core transformer"
→ IEEE C57.12.00: General requirements (일반 요구사항)
→ IEEE C57.104: Diagnostic methods (진단 방법)

Search 3: "CIGRE core transformer failure statistics"
→ CIGRE TB 642: Core failure rate 0.05%/year
→ CIGRE TB 393: Reliability survey data

Search 4: "Transformer Magazine core failure case study"
→ Case: 적층 절연 코팅 열화로 인한 와전류 손실 증가
→ Root cause: 제작 시 적층 압착력 부족

Search 5: "core transformer common failures root cause"
→ Core bolt insulation failure (볼트 절연 불량)
→ Multi-point grounding (다점 접지)
→ Lamination degradation (적층 열화)
```

### 2. 검색 결과 정리

```
[설계 기준 및 표준]
1. 자속 밀도 한계 ≤1.7T (IEC 60076-1)
2. 단락 내전력 기준 (IEC 60076-5)
3. 전기강판 자기 특성 (IEC 60404-8-4)

[고장 형태 및 패턴]
1. 층간 단락 (IEEE C57.125 분석 방법)
2. 다점 접지 (IEEE C57.125, CIGRE TB 642)
3. 와전류 증가 (IEEE C57.125 진단 결과)
4. 절연 열화 (Transformer Magazine 사례)

[고장 원인]
1. 설계: 적층 절연 코팅 두께 설계 오류 (Transformer Magazine)
2. 재료: 규소강판 재질 불량 (IEC 60404-8-4)
3. 제작: 적층 압착력 부족 (Transformer Magazine Case)
4. 시험: 무부하 손실 측정 누락 (IEEE C57.104)

[예방 대책]
1. 설계 기준 준수: 자속 밀도 ≤1.7T (IEC 60076-1)
2. 규소강판 절연 코팅 두께 검증 ≥2μm (IEC 60076-5)
3. 적층 압착력 관리 2500kN±10% (Transformer Magazine)
4. 단락 내전력 검증 (IEC 60076-5)

[검출 대책]
1. 무부하 손실 측정 (IEEE C57.104)
2. 역률 시험 (IEEE C57.104)
3. 철심 접지 전류 측정 (IEEE C57.125)
4. 접지 고장 진단 (IEEE C57.104)
```

### 3. FMEA 항목 생성

```
부품명: CORE
기능: 자속 전달
고장 영향: 와전류 손실 증가
고장 형태: 저하
고장 원인: 설계: 적층 절연 코팅 두께 설계 오류
고장 메커니즘: 절연 코팅 열화 → 층간 단락 → 와전류 손실 증가
현재 예방 대책: 설계 기준 준수 (자속 밀도 ≤1.7T, IEC 60076-1) + 규소강판 절연 코팅 두께 검증 (≥2μm, IEC 60076-5)
현재 검출 대책: 무부하 손실 측정 (IEEE C57.104) + 역률 시험 (IEEE C57.104)
S: 7, O: 2, D: 3, AP: M

Excel Row 3: 자료 출처: IEC 60076-1, IEC 60076-5, IEC 60404-8-4, IEEE C57.125, IEEE C57.104, CIGRE TB 642, Transformer Magazine, Claude 전문 지식
([!] 주의: 실제 사용한 출처만 명시, 위는 예시일 뿐!)
```

---

## [!] 주의사항

1. **모든 출처 필수**: 5개 중 1개라도 빠지면 안 됨
2. **검색 순서 준수**: 표준 → 통계 → 사례 순
3. **출처 명시 필수**: Excel Row 3에 실제 사용한 출처만 기재
4. **표준 용어 사용**: IEC/IEEE 표준 용어 우선
5. **비현실적 시나리오 제거**: 표준/문헌에 없는 고장 형태 배제
