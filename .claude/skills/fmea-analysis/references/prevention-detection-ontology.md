# 예방/검출대책 온톨로지 (Prevention-Detection Ontology)

**목적**: validate_prevention_detection.py의 출처/기준값/형식 규칙을 동적으로 로드

**적용**: `scripts/validate_prevention_detection.py`의 `load_prevention_detection_ontology()` 함수에서 파싱

**원리**: SSOT - 이 파일이 H열(현재예방대책)/J열(현재검출대책) 검증 규칙의 단일 진실 원천

---

## SECTION:REQUIRED_STAGES

설계, 재료, 제작, 시험

---

## SECTION:SOURCE_PATTERNS

### 내부문서 (1순위)
W시리즈: IEQT-T-W
R시리즈: IEQT-T-R
I시리즈: IEQT-T-I
P시리즈: IEQT-T-P
C시리즈: IEQT-T-C
TD시리즈: TD-
CHECK_SHEET: CHECK SHEET, CHECK_SHEET, 체크시트

### 외부표준 (2순위 - 선택사항)
IEC: IEC 60
IEEE: IEEE C57
CIGRE: CIGRE

### 일반 (3순위)
일반: 일반

> **[!!] 외부표준은 선택사항!** 내부문서 출처가 있으면 외부표준 없어도 됨

---

## SECTION:SOURCE_FORMAT_RULES

필수형식: (문서번호 섹션번호)
섹션기호: §
내부문서예시: (IEQT-T-W030 §3.2), (W018 §3.1), (권선 CHECK SHEET 권선조립-No.3)
외부표준예시: (IEC 60076-5 §8.2), (IEEE C57.12.00 §6.3)
일반예시: (일반)
CHECK_SHEET예시: (중신 CHECK SHEET 철심조립-No.5), (권선 CHECK SHEET 권선조립-No.3)

---

## SECTION:FORBIDDEN_SOURCE_PATTERNS

> **[!!] 금지 패턴은 "단독 사용" 시에만 적용!**
> - "P시리즈" 단독 금지 -> "(IEQT-T-P030 §3.2)" 허용!
> - 문서번호(IEQT-T-*)가 포함되면 금지 패턴 우회

일반용어금지: 작업표준, 검사기준, 시험요령, 기술기준, 설계기준, 품질기준
약어금지: CS, R-시리즈, W-시리즈
카테고리명금지: 권선CS, 단자CS, 중신CS, 외함CS
불완전출처: 작업표준 준수, 검사기준 준수, 표준 준수, 기준 준수

> **허용 패턴 (문서번호 포함 시):**
> - (IEQT-T-P030 §3.2) - 허용!
> - (IEQT-T-W018 시험요령) - 허용!
> - (IEQT-T-R012 검사기준) - 허용!

---

## SECTION:REQUIRED_VALUE_PATTERNS

토크값: N.m, N.M, Nm, kgf.m, kgf.cm
온도값: °C, 도C, 도씨
압력값: MPa, kPa, bar, kg/cm2, kgf/cm2
저항값: ohm, mOhm, uOhm, Mohm
전압값: kV, V, mV
전류값: A, mA, kA
시간값: 분, 초, 시간, hr, min, sec, s
비율값: %, 퍼센트
치수값: mm, cm, m, um
주기값: 개월, 년, 회

---

## SECTION:VALUE_FORMAT_EXAMPLES

토크: 45±5 N.m, 50 N.m 이상, 30~50 N.m
온도: 105±5°C, 80°C 이하, 60~80°C
저항: 110% 이하, 모재 저항의 110% 이하
비율: ±0.5%, 3% 이내, 5% 미만
치수: 0.3mm 이하, 1~2mm, ±0.1mm
주기: 6개월, 1년, 매 작업시

---

## SECTION:FORBIDDEN_VAGUE_EXPRESSIONS

수치없음: 적정, 적절, 충분, 양호, 정상, 확인, 검사, 점검, 관리
비교없음: 이상, 이하, 초과, 미만
목표없음: 기준대로, 표준대로, 규정대로, 요령대로

---

## SECTION:ABBREVIATION_MAP

CS: CHECK SHEET
R-: IEQT-T-R
W-: IEQT-T-W
I-: IEQT-T-I
P-: IEQT-T-P
C-: IEQT-T-C

---

## SECTION:CONTENT_STRUCTURE

H열형식: [단계]: [예방활동]\n- [세부내용1] ([출처])\n- [세부내용2] ([출처])
J열형식: [단계]: [검출방법]\n- [세부내용1] ([출처])\n- [세부내용2] ([출처])
단계태그: 설계:, 재료:, 제작:, 시험:

---

## SECTION:VALIDATION_RULES

> **[!!] 핵심: 모든 항목에 출처/기준값 필수 아님! FMEA 목적이 이것을 찾는 것!**

출처검증_권장: 내부문서(IEQT-T-*, TD-*, CHECK SHEET) 있으면 좋음 - WARNING (ERROR 아님!)
출처검증_선택: 외부표준(IEC, IEEE, CIGRE) 있으면 좋지만 없어도 OK
기준값검증: 정량적 기준값 권장 (수치+단위) - WARNING (ERROR 아님)
형식검증: [단계]: [대책] 형식 필수
약어검증: ABBREVIATION_MAP의 약어 사용 시 -> 정식명칭으로 변환
금지어검증: 문서번호 없이 금지어 단독 사용 시만 -> 오류

> **[!!] FMEA 목적**: 현재 예방/검출 대책이 없는 항목을 찾기 위한 것!
> 모든 항목에 출처가 있을 수 없음 - 없는 항목 발견이 FMEA 가치!

> **검증 우선순위**:
> 1. 형식 검증 (ERROR) - [단계]: [대책] 형식
> 2. 금지 패턴 검증 (ERROR - 문서번호 없이 단독 사용 시)
> 3. 내부문서 출처 검증 (WARNING - 없어도 진행!)
> 4. 기준값 검증 (WARNING - 없어도 진행!)
> 5. 외부표준 출처 검증 (INFO - 권장사항)

---

## SECTION:SEVERITY_LEVELS

ERROR: 출처 완전 누락, 금지 패턴 사용, 형식 위반
WARNING: 기준값 누락, 약어 사용, 섹션번호 누락
INFO: 일반 출처 사용 (내부문서 우선 권장)

---

## 파싱 규칙

- `## SECTION:<섹션명>` 형식으로 섹션 구분
- `### <하위섹션명>` 형식으로 하위 섹션 구분
- `카테고리: 값1, 값2, ...` 형식으로 값 나열
- 빈 줄로 섹션 간 구분

---

## 검증 예시

### [OK] 올바른 예시
```
제작: 토크렌치 사용 및 토크값 기록
- 토크렌치 교정 주기 6개월 (IEQT-T-W018 §3.2)
- 목표 토크값 45±5 N.m (권선 CHECK SHEET 권선조립-No.3)
- 체결 순서 대각선 방식 (일반)
```

### [X] 잘못된 예시
```
제작: 토크렌치 사용 (작업표준)        <- 금지! 문서번호 없음
- 적정 토크값 확인                   <- 금지! 수치 없음
- 체결 확인 (CS)                     <- 금지! 약어 사용
```

---

## 버전 관리

**버전**: 1.1
**작성일**: 2026-01-30
**변경 이력**:
- v1.0: 초기 버전 - H열/J열 검증 규칙 정의
- v1.1: 출처 검증 규칙 완화
  - 내부문서 출처 필수, 외부표준 선택사항
  - IEC 패턴 확장 (IEC 60 -> 모든 IEC 60xxx 매칭)
  - 금지 패턴 로직 개선 (문서번호 있으면 우회)
