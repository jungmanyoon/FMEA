# 기능-고장영향 온톨로지 (Function-Effect Ontology)

**목적**: 기능 키워드에서 관련 고장영향 키워드 매핑

**적용**:
- `scripts/validate_core_fmea.py`의 `load_function_effect_keywords()` 함수
- `scripts/analyze_causal_relationships.py`의 인과관계 검증

**원리**: SSOT - 이 파일이 기능-고장영향 키워드 매핑의 단일 진실 원천

---

## SECTION:FUNCTION_EFFECT_KEYWORDS

자속: 전압, 변환, 손실, 효율, 여자전류, 무부하, 철손, 와전류
지지: 변형, 진동, 소음, 정렬, 정밀도, 좌굴, 처짐, 붕괴
절연: 지락, 절연, 전기, 절연저항, 파괴, 단락, 방전, 누전
냉각: 과열, 온도, 열, 화재, 소손, 열화, 온도상승
고정: 이완, 이동, 변위, 탈락, 풀림, 체결
밀봉: 누유, 누기, 침수, 오일, 누출
접지: 다점접지, 순환전류, 접지불량, 접지
압축: 압축력, 이완, 갭, 간극, 접촉

## SECTION:LIFECYCLE_STAGES

설계: 설계 단계 고장 (치수 오류, 재료 선정 오류, 사양 미달)
재료: 재료 특성 고장 (재료 결함, 규격 미달, 순도 불량)
제작: 제조 공정 고장 (가공 오류, 조립 오류, 용접 불량)
시험: 시험/커미셔닝 고장 (시험 중 파손, 운송 손상, 설치 오류)

---

## 파싱 규칙

- `## SECTION:<섹션명>` 형식으로 섹션 구분
- `키워드: 관련어1, 관련어2, ...` 형식으로 매핑 정의
- `scripts/validate_core_fmea.py`와 `scripts/analyze_causal_relationships.py`에서 공통 로드

---

## 버전 관리

**버전**: 1.0
**작성일**: 2026-01-11
**변경 이력**:
- v1.0: 초기 버전 - validate_core_fmea.py, analyze_causal_relationships.py 하드코딩 데이터 외부화
