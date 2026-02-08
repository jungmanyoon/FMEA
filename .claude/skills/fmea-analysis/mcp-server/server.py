#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FMEA MCP Server - 변압기 FMEA 검증 도구

버전: 2.5
작성일: 2026-02-08
프레임워크: FastMCP v2.x

[!] v2.5 변경사항 (E열 추상적 표현 금지어 4카테고리 추가):
- E열: 추상적표현(불량/이상/미흡) + 힘(체결력 등 8개) + 물성(기밀성 등 7개) + 기능(5개) 추가
- failure-mode-ontology.md FORBIDDEN_PATTERNS 전수 동기화
[!] v2.4: E열 메커니즘 4개 + C열 물리상태/검사결과 + G열 unicode arrow/원인키워드
- H/J열: 라이프사이클 태그 2개 이상 강제 (v2.3)
[!] v2.2: C/F열 상세설명 검증
[!] v2.1: E열 3줄 구조 강제
[!] v2.0: 신규 도구 3개 + 강화 도구 4개 + 키워드 매핑
"""

import json
import hashlib
from pathlib import Path
from typing import Optional

# [O] 올바른 FastMCP import (팩트체크 반영)
from fastmcp import FastMCP

# ============================================================
# 경로 설정
# ============================================================

# 스킬 루트 경로 (mcp-server의 상위)
SKILL_ROOT = Path(__file__).parent.parent
SCRIPTS_PATH = SKILL_ROOT / "scripts"
REFERENCES_PATH = SKILL_ROOT / "references"

# ============================================================
# 내장 검증 구현 (외부 의존성 제거)
# ============================================================
# [O] 모든 검증 로직은 _validate_*_logic 함수로 내장 구현
# [O] scripts/ 폴더 함수와 동일한 규칙 적용

# ============================================================
# MCP 서버 생성
# ============================================================

mcp = FastMCP("fmea-mcp")

# ============================================================
# 전역 상태 (환각 방지용)
# ============================================================

# 읽은 파일 기록 (세션 내 유지)
_read_files: dict = {}  # {file_path: content_hash}

# ============================================================
# 금지어 목록 (온톨로지 파일 없을 때 폴백)
# ============================================================

# E열 금지어 - 메커니즘 (G열로 이동 필요)
# [v2.4] 온톨로지 파일과 동기화: 열팽창/열수축/와전류/히스테리시스 추가
FORBIDDEN_MECHANISMS = [
    "피로", "응력집중", "크리프", "열화진행", "열피로",
    "산화", "가수분해", "전기적트리", "부분방전", "열화",
    "마모", "침식", "부식진행", "절연열화",
    "열팽창", "열수축", "와전류", "히스테리시스"
]

# E열 금지어 - 측정값 (G열로 이동 필요)
FORBIDDEN_MEASUREMENTS = [
    "증가", "저하", "상승", "감소", "철손증가", "효율저하",
    "온도상승", "전류증가", "손실증가", "저항증가"
]

# E열 금지어 - 미래결과 (C열로 이동 필요)
FORBIDDEN_FUTURE_RESULTS = [
    "소음", "진동", "오작동", "트립", "정전", "과열",
    "화재", "폭발", "정지", "고장"
]

# [v2.5] E열 금지어 - 추상적 표현 (눈에 보이는 현상으로 교체 필요)
# failure-mode-ontology.md FORBIDDEN_PATTERNS 동기화
FORBIDDEN_ABSTRACTIONS = ["불량", "이상", "미흡"]

# [v2.5] E열 금지어 - 힘/강도 패턴 (측정 장비 필요 -> VISIBILITY_RULE 위반)
FORBIDDEN_FORCES = [
    "체결력", "고정력", "압착력", "클램핑력",
    "접촉력", "밀착력", "조임력", "결합력"
]

# [v2.5] E열 금지어 - 물성 패턴 (측정 장비 필요 -> VISIBILITY_RULE 위반)
FORBIDDEN_PROPERTIES = [
    "기밀성", "절연성", "내구성", "접착성",
    "유연성", "강성", "경도"
]

# [v2.5] E열 금지어 - 기능/성능 패턴 (추상적 개념 -> 구체적 현상으로)
FORBIDDEN_FUNCTIONS = ["기능", "성능", "효율", "용량", "능력"]

# 필수 태그
REQUIRED_TAGS = ["부족:", "과도:", "유해:"]

# 라이프사이클 태그
LIFECYCLE_TAGS = ["설계:", "재료:", "제작:", "시험:"]

# 인과관계 금지 조합
INVALID_CAUSAL_COMBINATIONS = {
    "층간단락": ["턴수설계오류", "턴수계수오류", "전압비계산오류", "권선수오류"],
    "지락": ["턴수설계오류", "턴수계수오류", "전압비계산오류"],
    "절연파괴": ["턴수설계오류", "전압비계산오류"],
    "변형": ["절연열화", "수분침입", "과전압", "부분방전"],
    "이완": ["절연열화", "과전압", "과전류"],
    "누유": ["과전압", "과전류", "절연열화"],
}

# ============================================================
# 키워드 매핑 테이블 (맥락 검증용) [v2.0 신규]
# ============================================================

# B->C: 기능 키워드 -> 허용 영향 키워드
FUNCTION_EFFECT_MAP = {
    "전류": ["전류", "통전", "저항", "개방"],
    "경로": ["전류", "통전", "저항", "개방"],
    "자속": ["전압", "변환", "손실", "효율", "여자전류"],
    "자기장": ["전압", "변환", "손실", "효율", "여자전류"],
    "절연": ["절연", "단락", "지락", "방전"],
    "내력": ["절연", "단락", "지락", "방전"],
    "지지": ["변형", "진동", "소음", "정렬"],
    "견딘다": ["변형", "진동", "소음", "정렬"],
    "냉각": ["과열", "온도", "열"],
    "방열": ["과열", "온도", "열"],
    "밀봉": ["누유", "누설", "유면"],
    "실링": ["누유", "누설", "유면"],
}

# E->J: 형태 키워드 -> 적합 검출 키워드
MODE_DETECTION_MAP = {
    "단선": ["통전", "저항", "연속성", "FRA"],
    "끊어짐": ["통전", "저항", "연속성", "FRA"],
    "이완": ["토크", "육안", "체결"],
    "풀림": ["토크", "육안", "체결"],
    "크랙": ["초음파", "방사선", "육안", "침투"],
    "균열": ["초음파", "방사선", "육안", "침투"],
    "누유": ["압력", "기밀", "육안", "가스검출"],
    "누설": ["압력", "기밀", "육안", "가스검출"],
    "변형": ["치수", "레이저", "육안", "정밀측정"],
    "뒤틀림": ["치수", "레이저", "육안", "정밀측정"],
    "절연손상": ["내전압", "부분방전", "절연저항", "tan-delta"],
    "피복": ["내전압", "부분방전", "절연저항", "tan-delta"],
    "층간이격": ["유도내전압", "상용주파", "부분방전"],
    "턴수오류": ["전압비", "무부하", "극성"],
}

# F->H: 원인 키워드 -> 적합 예방 키워드
CAUSE_PREVENTION_MAP = {
    "용접": ["온도관리", "브레이징", "타격시험", "용접"],
    "브레이징": ["온도관리", "브레이징", "타격시험", "용접"],
    "동선": ["수입검사", "치수확인", "외관검사", "성적서"],
    "도체": ["수입검사", "치수확인", "외관검사", "성적서"],
    "스페이서": ["배치확인", "치수검사", "절연설계"],
    "절연물": ["배치확인", "치수검사", "절연설계"],
    "체결": ["토크관리", "체결확인", "마킹"],
    "볼트": ["토크관리", "체결확인", "마킹"],
    "피복": ["외관검사", "두께측정", "취급주의"],
    "코팅": ["외관검사", "두께측정", "취급주의"],
    "설계": ["설계리뷰", "검증", "체크시트"],
    "계산": ["설계리뷰", "검증", "체크시트"],
}

# C->E: 영향 키워드 -> 허용 형태 키워드 [v2.0 C->E 검증]
EFFECT_MODE_MAP = {
    "통전": ["단선", "끊어짐", "개방", "접촉불량", "저항"],
    "절연파괴": ["절연손상", "피복손상", "층간", "크랙", "이격"],
    "단락": ["절연손상", "피복손상", "층간", "크랙", "단락"],
    "지락": ["절연손상", "피복손상", "크랙", "지락"],
    "변형": ["이완", "뒤틀림", "변위", "탈락", "크랙", "변형"],
    "진동": ["이완", "뒤틀림", "변위", "탈락"],
    "소음": ["이완", "뒤틀림", "변위", "탈락"],
    "과열": ["단선", "접촉불량", "냉각", "유로", "온도"],
    "누유": ["크랙", "균열", "체결불량", "가스켓", "누유"],
    "누설": ["크랙", "균열", "체결불량", "가스켓", "누설"],
    "손실": ["턴수", "치수", "편차"],
    "효율": ["턴수", "치수", "편차"],
}

# 도메인 분류 (F-G 도메인 일치 검증용)
DOMAIN_CATEGORIES = {
    "electrical": [
        "전류", "전압", "저항", "절연", "단락", "지락", "방전", "과전압", "과전류", "내전압",
        "동선", "도체", "소선", "CTC", "권선", "통전", "개방", "턴수", "피복", "코팅",
        "부분방전", "유도", "극성", "여자전류", "상용주파",
    ],
    "mechanical": [
        "체결", "볼트", "토크", "진동", "변형", "이완", "탈락", "파손", "파단", "좌굴",
        "스페이서", "정렬", "뒤틀림", "크랙", "균열", "충격", "기계력",
    ],
    "thermal": ["온도", "과열", "열화", "열팽창", "열수축", "냉각", "발열", "열사이클", "브레이징"],
    "chemical": ["부식", "산화", "가수분해", "오염"],
    "fluid": ["누유", "누설", "유면", "유량", "유압", "침습", "유중가스", "DGA"],
}

# 라이프사이클별 키워드 (F-G 라이프사이클 일치 검증용)
LIFECYCLE_KEYWORDS = {
    "설계": ["설계", "계산", "사양", "도면", "마진"],
    "재료": ["재료", "원자재", "수입", "성분", "내부결함"],
    "제작": ["작업", "조립", "용접", "제작", "가공", "취급", "브레이징"],
    "시험": ["시험", "측정", "검사", "테스트"],
}

# F->G 금지 조합 (원인 키워드 -> 메커니즘에 나오면 안되는 키워드)
INVALID_CAUSE_MECHANISM_COMBINATIONS = {
    "턴수": ["체결", "토크", "용접", "브레이징"],
    "전압비": ["체결", "토크", "용접", "브레이징"],
    "절연설계": ["체결", "토크", "용접"],
    "토크": ["절연열화", "부분방전", "전기적트리"],
    "체결": ["절연열화", "부분방전", "전기적트리"],
    "용접": ["절연열화", "부분방전", "전기적트리", "턴수"],
    "수입검사": ["설계마진", "설계리뷰"],
    "재료": ["설계마진", "계산오류"],
    # 도체-절연 도메인 분리 (electrical 하위 구분)
    "동선": ["부분방전", "절연파괴", "절연열화", "절연 코팅"],
    "도체": ["부분방전", "절연파괴", "절연열화", "절연 코팅"],
    "소선": ["부분방전", "절연파괴", "절연열화", "절연 코팅"],
    "CTC": ["부분방전", "절연파괴", "절연열화", "절연 코팅"],
}

# ============================================================
# 검증 로직 (순수 함수 - 테스트 가능)
# ============================================================

def _validate_failure_mode_logic(failure_mode: str) -> dict:
    """E열 검증 로직 (내부 함수)

    [v2.1] 3줄 구조(옵션 A) 강제 검증 추가
    - 1줄: 태그 + 현상 (금지어 검증 대상)
    - 2줄: (상세 설명) - 존재 여부만 검증
    - 3줄: (판단 근거) - 존재 여부만 검증
    - 금지어 검증은 1줄에만 적용 (온톨로지 규칙)
    """
    violations = []
    suggestions = []

    # [v2.1] 줄 분리 - 1줄만 검증 (failure-mode-ontology.md 규칙)
    lines = failure_mode.split("\n")
    first_line = lines[0].strip()

    # 1. 태그 검증 (1줄에서만)
    has_tag = any(tag in first_line for tag in REQUIRED_TAGS)
    if not has_tag:
        violations.append({
            "type": "MISSING_TAG",
            "message": "필수 태그 누락: 부족:/과도:/유해: 중 하나 필요"
        })
        suggestions.append("형식: '[부족|과도|유해]: [눈에 보이는 현상]'")

    # 2. 메커니즘 금지어 검증 (1줄에서만)
    for mechanism in FORBIDDEN_MECHANISMS:
        if mechanism in first_line:
            violations.append({
                "type": "MECHANISM_IN_E",
                "word": mechanism,
                "message": "'%s'은 메커니즘(과정)! G열로 이동 필요" % mechanism
            })
            suggestions.append("E열: '눈에 보이는' 현상만 / G열: '%s' 포함" % mechanism)

    # 3. 측정값 금지어 검증 (1줄에서만)
    for measurement in FORBIDDEN_MEASUREMENTS:
        if measurement in first_line:
            violations.append({
                "type": "MEASUREMENT_IN_E",
                "word": measurement,
                "message": "'%s'은 측정값! G열로 이동 필요" % measurement
            })

    # 4. 미래결과 금지어 검증 (1줄에서만)
    for future in FORBIDDEN_FUTURE_RESULTS:
        if future in first_line:
            violations.append({
                "type": "FUTURE_RESULT_IN_E",
                "word": future,
                "message": "'%s'은 미래 결과! C열로 이동 필요" % future
            })

    # 5. [v2.5 NEW] 추상적 표현 금지어 검증 (1줄에서만)
    # failure-mode-ontology.md FORBIDDEN_PATTERNS 동기화
    # 복합어 예외: 접촉불량, 밀착불량, 용접불량, 적층불량 등은 유효한 visible phenomena
    ABSTRACT_COMPOUND_EXCEPTIONS = [
        "접촉불량", "밀착불량", "용접불량", "적층불량",
        "가공불량", "압착불량", "체결불량", "조립불량"
    ]
    for abstract in FORBIDDEN_ABSTRACTIONS:
        if abstract in first_line:
            # 복합어 예외 확인: "불량"이 복합어의 일부이면 허용
            is_compound = any(comp in first_line for comp in ABSTRACT_COMPOUND_EXCEPTIONS
                             if abstract in comp)
            if is_compound:
                continue
            violations.append({
                "type": "ABSTRACT_IN_E",
                "word": abstract,
                "message": "'%s'은 추상적 표현! 눈에 보이는 구체적 현상으로 교체 "
                           "(예: 크랙, 이완, 변색, 탈락)" % abstract
            })
            suggestions.append(
                "E열: 눈에 보이는 현상 / '%s' -> 크랙, 이완, 변형, 탈락 등" % abstract)

    # 6. [v2.5 NEW] 힘/강도 패턴 금지어 검증 (측정 장비 필요)
    for force in FORBIDDEN_FORCES:
        if force in first_line:
            # ABSTRACT_TO_VISIBLE_MAP 기반 대체 제안
            alt_map = {
                "체결력": "풀림, 이완, 헐거움",
                "고정력": "이완, 변위, 탈락",
                "압착력": "이격, 분리, 밀착불량",
                "클램핑력": "이완, 변위, 풀림",
                "접촉력": "접촉불량, 이격, 아크흔적",
                "밀착력": "이격, 분리, 간극발생",
                "조임력": "풀림, 이완, 헐거움",
                "결합력": "분리, 이격, 탈락",
            }
            violations.append({
                "type": "FORCE_IN_E",
                "word": force,
                "message": "'%s'은 측정 장비 필요! 눈에 보이는 결과로 교체 필요" % force
            })
            alt = alt_map.get(force, "이완, 풀림, 탈락")
            suggestions.append("E열: '%s' -> %s" % (force, alt))

    # 7. [v2.5 NEW] 물성 패턴 금지어 검증 (측정 장비 필요)
    for prop in FORBIDDEN_PROPERTIES:
        if prop in first_line:
            alt_map = {
                "기밀성": "누설, 누유, 기포",
                "절연성": "탄화, 변색, 아크흔적",
                "내구성": "균열, 마모, 변형",
                "접착성": "박리, 벗겨짐, 분리",
                "유연성": "균열, 파손, 크랙",
                "강성": "변형, 뒤틀림, 휨",
                "경도": "마모, 흠집, 스크래치",
            }
            violations.append({
                "type": "PROPERTY_IN_E",
                "word": prop,
                "message": "'%s'은 측정 필요한 물성! 눈에 보이는 결과로 교체 필요" % prop
            })
            alt = alt_map.get(prop, "균열, 변형, 마모")
            suggestions.append("E열: '%s' -> %s" % (prop, alt))

    # 8. [v2.5 NEW] 기능/성능 패턴 금지어 검증 (추상적 개념)
    for func in FORBIDDEN_FUNCTIONS:
        if func in first_line:
            violations.append({
                "type": "FUNCTION_IN_E",
                "word": func,
                "message": "'%s'은 추상적 개념! E열은 눈에 보이는 현상만 "
                           "(C열: 기능 실패 결과 / E열: 물리적 현상)" % func
            })
            suggestions.append(
                "E열: 눈에 보이는 현상 / '%s' -> 이완, 변형, 탈락, 균열 등" % func)

    # 9. [v2.1] 3줄 구조 (옵션 A) 강제 검증
    # 2줄: (상세 설명) 필수
    has_detail = (len(lines) >= 2
                  and lines[1].strip().startswith("(")
                  and lines[1].strip().endswith(")"))
    if not has_detail:
        violations.append({
            "type": "MISSING_DETAIL",
            "message": "E열 2줄 괄호 상세 설명 누락! "
                       "옵션 A 형식: 태그: 현상\\n(상세 설명)\\n(판단 근거)"
        })
        suggestions.append(
            "예시: 부족: 볼트 이완\\n"
            "(체결부 볼트가 풀리는 현상)\\n"
            "(부족: 구조적 연결이 부족하면 볼트 이완 발생)")

    # 3줄: (판단 근거) 필수
    has_judgment = (len(lines) >= 3
                    and lines[2].strip().startswith("(")
                    and lines[2].strip().endswith(")"))
    if has_detail and not has_judgment:
        violations.append({
            "type": "MISSING_JUDGMENT",
            "message": "E열 3줄 판단 근거 누락! "
                       "형식: (부족/과도/유해: [기능 결과물]이 ...하면 [현상] 발생)"
        })

    # 3줄 판단 근거에 태그 포함 여부 확인
    if has_judgment and has_tag:
        used_tag = None
        for tag in REQUIRED_TAGS:
            if tag in first_line:
                used_tag = tag
                break
        if used_tag and used_tag not in lines[2]:
            violations.append({
                "type": "TAG_MISMATCH_JUDGMENT",
                "message": "3줄 판단 근거의 태그('%s')가 1줄 태그와 불일치" % used_tag
            })

    return {
        "status": "pass" if not violations else "fail",
        "input": failure_mode,
        "first_line": first_line,
        "line_count": len(lines),
        "has_detail": has_detail,
        "has_judgment": has_judgment,
        "violations": violations,
        "suggestions": suggestions,
        "violation_count": len(violations)
    }


def _validate_effect_logic(effect: str) -> dict:
    """C열 검증 로직 (내부 함수)
    - v2.2: 상세설명 검증 추가 (260207)
    - v2.4: 물리상태 5개 추가 + 검사결과 금지어 추가 (260208)
    """
    violations = []
    suggestions = []

    # 1. 상세설명 존재 검증 (C열: "영향\n(상세설명)" 2줄 형식)
    if "\n" not in effect:
        violations.append({
            "type": "MISSING_DETAIL",
            "message": "C열 상세설명 누락! 2줄 형식 필수: '영향\\n(상세설명)'"
        })
        suggestions.append("예시: '절연파괴\\n(유전체 강도 초과로 인한 지락)'")
    else:
        lines = [l.strip() for l in effect.split("\n") if l.strip()]
        if len(lines) >= 2:
            second_line = lines[1]
            if not (second_line.startswith("(") and second_line.endswith(")")):
                violations.append({
                    "type": "DETAIL_FORMAT",
                    "message": "C열 2줄째는 (상세설명) 형식이어야 함"
                })
                suggestions.append(
                    "2줄째를 괄호로 감싸세요: '(%s)'" % second_line[:30]
                )

    # 2. 물리적 상태 검증 (1줄째만 대상)
    # [v2.4] effect-ontology.md와 동기화: 균열/누설/마모/변색/산화 추가
    physical_states = [
        "크랙", "변형", "단락", "파손", "이완", "탈락",
        "누유", "부식", "오염", "손상",
        "균열", "누설", "마모", "변색", "산화"
    ]

    first_line = effect.split("\n")[0].strip() if "\n" in effect else effect
    for state in physical_states:
        if state in first_line:
            violations.append({
                "type": "PHYSICAL_STATE_IN_C",
                "word": state,
                "message": "'%s'은 물리적 상태! E열로 이동 필요" % state
            })
            suggestions.append("C열: 미래 영향 / E열: '%s' (현재 상태)" % state)

    # 3. [v2.4 NEW] 검사/판정 결과 금지어 (C열은 기술적 영향이어야 함)
    forbidden_results = [
        "FAT 불합격", "FAT불합격", "시험 불합격", "시험불합격",
        "부적합", "조립불합격", "용접불합격", "외관불합격",
        "검사 불합격", "불합격"
    ]
    for result in forbidden_results:
        if result in first_line:
            violations.append({
                "type": "TEST_RESULT_IN_C",
                "word": result,
                "message": "'%s'은 검사/판정 결과! 기술적 영향으로 변경 필요" % result
            })
            suggestions.append(
                "C열: 기술적 영향 (예: 절연파괴, 과열) / '%s'은 판정 용어" % result
            )

    return {
        "status": "pass" if not violations else "fail",
        "input": effect,
        "violations": violations,
        "suggestions": suggestions
    }


def _validate_cause_logic(cause: str) -> dict:
    """F열 검증 로직 (내부 함수) - v2.2: 상세설명 검증 추가 (260207)"""
    violations = []
    suggestions = []

    # 1. 라이프사이클 태그 검증 (기존 로직)
    has_lifecycle = any(tag in cause for tag in LIFECYCLE_TAGS)
    if not has_lifecycle:
        violations.append({
            "type": "MISSING_LIFECYCLE",
            "message": "라이프사이클 태그 필수: 설계:/재료:/제작:/시험: 중 하나"
        })
        suggestions.append("형식: '[설계|재료|제작|시험]: [과거 원인]'")

    # 2. 상세설명 존재 검증 (F열: "단계: 원인\n(상세설명)" 2줄 형식)
    if "\n" not in cause:
        violations.append({
            "type": "MISSING_DETAIL",
            "message": "F열 상세설명 누락! 2줄 형식 필수: '단계: 원인\\n(상세설명)'"
        })
        suggestions.append(
            "예시: '설계: 수축율 미반영\\n(프레스보드 수축율 3-5%% 미고려)'"
        )
    else:
        lines = [l.strip() for l in cause.split("\n") if l.strip()]
        if len(lines) >= 2:
            second_line = lines[1]
            if not (second_line.startswith("(") and second_line.endswith(")")):
                violations.append({
                    "type": "DETAIL_FORMAT",
                    "message": "F열 2줄째는 (상세설명) 형식이어야 함"
                })
                suggestions.append(
                    "2줄째를 괄호로 감싸세요: '(%s)'" % second_line[:30]
                )

    return {
        "status": "pass" if not violations else "fail",
        "input": cause,
        "violations": violations,
        "suggestions": suggestions
    }


def _validate_mechanism_logic(mechanism: str) -> dict:
    """G열 검증 로직 (내부 함수)
    - v2.4: unicode arrow 지원 + 원인 키워드 금지 추가 (260208)
    """
    violations = []

    # [v2.4] -> 와 unicode arrow 모두 카운트
    arrow_count = mechanism.count("->") + mechanism.count("\u2192")

    if arrow_count < 2:
        violations.append({
            "type": "ARROW_COUNT",
            "current": arrow_count,
            "required": 2,
            "message": "화살표 2개 이상 필요 (현재: %d개). "
                       "형식: '원인 -> 과정 -> 결과'" % arrow_count
        })

    # [v2.4 NEW] G열에 원인 키워드(F열 용어) 금지
    # validate_single_item.py와 동기화
    cause_keywords_in_g = [
        "설계 오류", "재료 불량", "조립 오차", "검증 누락", "가공 불량",
        "치수 오차", "용접 불량", "체결 불량", "인장 파괴", "피로 파괴"
    ]
    mech_stripped = mechanism.strip()
    for keyword in cause_keywords_in_g:
        if mech_stripped == keyword or mech_stripped == keyword.strip():
            violations.append({
                "type": "CAUSE_KEYWORD_IN_G",
                "word": keyword,
                "message": "G열에 원인 용어 '%s' 금지! -> F열로 이동. "
                           "G열은 메커니즘 체인: '원인 상태 -> 물리적 과정 -> 결과 상태'"
                           % keyword
            })

    return {
        "status": "pass" if not violations else "fail",
        "input": mechanism,
        "arrow_count": arrow_count,
        "violations": violations
    }


def _validate_prevention_logic(prevention: str, cause: Optional[str] = None) -> dict:
    """H열 검증 로직 (내부 함수) - v2.3: 라이프사이클 태그 수 검증 추가"""
    violations = []
    warnings = []
    lines = [l.strip() for l in prevention.split("\n") if l.strip()]
    line_count = len(lines)

    if line_count < 4:
        violations.append({
            "type": "LINE_COUNT",
            "current": line_count,
            "required": 4,
            "message": f"4줄 이상 필요 (현재: {line_count}줄)"
        })

    # v2.3: 라이프사이클 태그 수 검증 (최소 2단계 필수)
    lifecycle_stages = ["설계:", "재료:", "제작:", "시험:"]
    found_stages = [s for s in lifecycle_stages
                    if any(s in line for line in lines)]
    if len(found_stages) < 2:
        violations.append({
            "type": "LIFECYCLE_TAG_COUNT",
            "current": len(found_stages),
            "found": [s.rstrip(":") for s in found_stages],
            "required": 2,
            "message": "라이프사이클 태그 2개 이상 필요 (현재: %d개 %s). "
                       "설계:/재료:/제작:/시험: 중 2개 이상 포함 필수"
                       % (len(found_stages),
                          [s.rstrip(":") for s in found_stages])
        })

    # v2.0: cause 맥락 검증
    if cause:
        relevance = _check_keyword_relevance(
            cause, prevention, CAUSE_PREVENTION_MAP,
            "F->H", "원인", "예방대책"
        )
        if relevance["status"] == "fail":
            warnings.extend([{**v, "severity": "WARNING"} for v in relevance["violations"]])

    result = {
        "status": "pass" if not violations else "fail",
        "input_preview": prevention[:100] + "..." if len(prevention) > 100 else prevention,
        "line_count": line_count,
        "violations": violations
    }
    if warnings:
        result["warnings"] = warnings
    return result


def _validate_detection_logic(detection: str, failure_mode: Optional[str] = None) -> dict:
    """J열 검증 로직 (내부 함수) - v2.3: 라이프사이클 태그 수 검증 추가"""
    violations = []
    warnings = []
    lines = [l.strip() for l in detection.split("\n") if l.strip()]
    line_count = len(lines)

    if line_count < 4:
        violations.append({
            "type": "LINE_COUNT",
            "current": line_count,
            "required": 4,
            "message": f"4줄 이상 필요 (현재: {line_count}줄)"
        })

    # v2.3: 라이프사이클 태그 수 검증 (최소 2단계 필수)
    lifecycle_stages = ["설계:", "재료:", "제작:", "시험:"]
    found_stages = [s for s in lifecycle_stages
                    if any(s in line for line in lines)]
    if len(found_stages) < 2:
        violations.append({
            "type": "LIFECYCLE_TAG_COUNT",
            "current": len(found_stages),
            "found": [s.rstrip(":") for s in found_stages],
            "required": 2,
            "message": "라이프사이클 태그 2개 이상 필요 (현재: %d개 %s). "
                       "설계:/재료:/제작:/시험: 중 2개 이상 포함 필수"
                       % (len(found_stages),
                          [s.rstrip(":") for s in found_stages])
        })

    # v2.0: failure_mode 맥락 검증
    if failure_mode:
        relevance = _check_keyword_relevance(
            failure_mode, detection, MODE_DETECTION_MAP,
            "E->J", "형태", "검출대책"
        )
        if relevance["status"] == "fail":
            warnings.extend([{**v, "severity": "WARNING"} for v in relevance["violations"]])

    result = {
        "status": "pass" if not violations else "fail",
        "input_preview": detection[:100] + "..." if len(detection) > 100 else detection,
        "line_count": line_count,
        "violations": violations
    }
    if warnings:
        result["warnings"] = warnings
    return result


def _validate_causal_chain_logic(failure_mode: str, cause: str) -> dict:
    """E->F 인과관계 검증 로직 (내부 함수)"""
    violations = []

    # 태그 제거
    mode_clean = failure_mode
    for tag in REQUIRED_TAGS:
        mode_clean = mode_clean.replace(tag, "").strip()

    cause_clean = cause
    for tag in LIFECYCLE_TAGS:
        cause_clean = cause_clean.replace(tag, "").strip()

    # 금지 조합 검증
    for mode_key, invalid_causes in INVALID_CAUSAL_COMBINATIONS.items():
        if mode_key in mode_clean:
            for invalid_cause in invalid_causes:
                if invalid_cause in cause_clean:
                    violations.append({
                        "type": "INVALID_CAUSAL_CHAIN",
                        "mode": mode_key,
                        "cause": invalid_cause,
                        "message": f"'{mode_key}' <- '{invalid_cause}' 인과관계 불성립!",
                        "reason": _get_causal_reason(mode_key, invalid_cause)
                    })

    return {
        "status": "pass" if not violations else "fail",
        "failure_mode": failure_mode,
        "cause": cause,
        "violations": violations
    }


def _get_causal_reason(mode: str, cause: str) -> str:
    """인과관계 불성립 이유 반환"""
    if mode in ["층간단락", "지락", "절연파괴"]:
        if "턴수" in cause or "전압비" in cause or "권선수" in cause:
            return "층간단락/지락은 절연 손상 문제, 턴수/전압비는 전기계산 문제 (별개 도메인)"
    if mode in ["변형", "이완", "탈락"]:
        if "절연" in cause or "과전압" in cause:
            return "기계적 고장(변형/이완)은 진동/응력이 원인, 절연/전기적 원인과 무관"
    return "도메인 불일치"


# ============================================================
# v2.0 신규 검증 로직 (맥락 검증)
# ============================================================

def _check_keyword_relevance(
    source: str, target: str, mapping: dict,
    check_name: str, source_label: str, target_label: str
) -> dict:
    """키워드 매핑 기반 연관성 검증 (F->H, E->J 공통 헬퍼)"""
    violations = []
    matched = []

    # 태그 제거
    source_clean = source
    for tag in REQUIRED_TAGS + LIFECYCLE_TAGS:
        source_clean = source_clean.replace(tag, "").strip()

    # source에서 알려진 키워드 찾기
    source_keywords_found = []
    for src_kw in mapping:
        if src_kw in source_clean:
            source_keywords_found.append(src_kw)

    if not source_keywords_found:
        return {
            "status": "pass",
            "violations": [],
            "warnings": [f"{source_label}에서 알려진 키워드를 찾을 수 없음 - 검증 생략"]
        }

    # target에서 매핑된 키워드 찾기
    for src_kw in source_keywords_found:
        expected = mapping[src_kw]
        for exp_kw in expected:
            if exp_kw in target:
                matched.append({"source": src_kw, "target": exp_kw})

    if not matched:
        violations.append({
            "type": f"{check_name.replace('->', '_').replace('>', '_')}_MISMATCH",
            "check": check_name,
            "source_keywords": source_keywords_found,
            "expected_target_keywords": list(set(
                kw for sk in source_keywords_found for kw in mapping[sk]
            )),
            "message": f"{source_label}({', '.join(source_keywords_found)})에 대한 {target_label}에 관련 키워드 없음"
        })

    return {
        "status": "pass" if not violations else "fail",
        "matched": matched,
        "violations": violations
    }


def _validate_cause_mechanism_logic(cause: str, mechanism: str) -> dict:
    """F->G 원인-메커니즘 도메인 일치 검증 [v2.0 신규]"""
    violations = []

    # 태그 제거
    cause_clean = cause
    for tag in LIFECYCLE_TAGS:
        cause_clean = cause_clean.replace(tag, "").strip()

    # 도메인 탐지
    cause_domains = set()
    mech_domains = set()

    for domain, keywords in DOMAIN_CATEGORIES.items():
        for kw in keywords:
            if kw in cause_clean:
                cause_domains.add(domain)
            if kw in mechanism:
                mech_domains.add(domain)

    # 도메인 교차 검증
    if cause_domains and mech_domains:
        overlap = cause_domains & mech_domains
        if not overlap:
            violations.append({
                "type": "DOMAIN_MISMATCH",
                "cause_domains": sorted(cause_domains),
                "mechanism_domains": sorted(mech_domains),
                "message": f"원인 도메인({', '.join(sorted(cause_domains))})과 "
                           f"메커니즘 도메인({', '.join(sorted(mech_domains))}) 불일치"
            })

    # 라이프사이클 일관성 검증
    cause_lifecycle = None
    for tag in LIFECYCLE_TAGS:
        if tag in cause:
            cause_lifecycle = tag.replace(":", "")
            break

    mech_lifecycle_hints = set()
    for lc, keywords in LIFECYCLE_KEYWORDS.items():
        for kw in keywords:
            if kw in mechanism:
                mech_lifecycle_hints.add(lc)

    if cause_lifecycle and mech_lifecycle_hints:
        if cause_lifecycle not in mech_lifecycle_hints and len(mech_lifecycle_hints) == 1:
            mech_lc = list(mech_lifecycle_hints)[0]
            violations.append({
                "type": "LIFECYCLE_MISMATCH",
                "cause_lifecycle": cause_lifecycle,
                "mechanism_lifecycle": mech_lc,
                "message": f"원인({cause_lifecycle})과 메커니즘({mech_lc}) 라이프사이클 불일치"
            })

    # 3. 금지 조합 검증 (INVALID_CAUSE_MECHANISM_COMBINATIONS)
    for cause_kw, invalid_mech_keywords in INVALID_CAUSE_MECHANISM_COMBINATIONS.items():
        if cause_kw in cause_clean:
            for inv_mech in invalid_mech_keywords:
                if inv_mech in mechanism:
                    violations.append({
                        "type": "INVALID_CAUSE_MECHANISM",
                        "cause_keyword": cause_kw,
                        "mechanism_keyword": inv_mech,
                        "message": f"원인 '{cause_kw}' <-> 메커니즘 '{inv_mech}' 금지 조합!"
                    })

    return {
        "status": "pass" if not violations else "fail",
        "cause": cause,
        "mechanism": mechanism,
        "cause_domains": sorted(cause_domains) if cause_domains else ["unknown"],
        "mechanism_domains": sorted(mech_domains) if mech_domains else ["unknown"],
        "violations": violations
    }


def _validate_function_effect_logic(function: str, effect: str) -> dict:
    """B->C 기능-영향 연관성 검증 [v2.0 신규]"""
    violations = []
    matched_keywords = []

    # 기능 키워드 찾기
    func_keywords_found = []
    for func_kw in FUNCTION_EFFECT_MAP:
        if func_kw in function:
            func_keywords_found.append(func_kw)

    if not func_keywords_found:
        return {
            "status": "pass",
            "function": function,
            "effect": effect,
            "violations": [],
            "warnings": ["기능에서 알려진 키워드를 찾을 수 없음 - 검증 생략"],
            "relevance_score": 0.5
        }

    # 영향에서 매핑된 키워드 찾기
    for func_kw in func_keywords_found:
        allowed_effect_keywords = FUNCTION_EFFECT_MAP[func_kw]
        for eff_kw in allowed_effect_keywords:
            if eff_kw in effect:
                matched_keywords.append({"function": func_kw, "effect": eff_kw})

    if not matched_keywords:
        violations.append({
            "type": "FUNCTION_EFFECT_MISMATCH",
            "function_keywords": func_keywords_found,
            "expected_effect_keywords": list(set(
                kw for fk in func_keywords_found for kw in FUNCTION_EFFECT_MAP[fk]
            )),
            "message": f"기능({', '.join(func_keywords_found)})과 영향의 연관성 없음"
        })

    relevance_score = min(1.0, len(matched_keywords) / max(1, len(func_keywords_found)))

    return {
        "status": "pass" if not violations else "fail",
        "function": function,
        "effect": effect,
        "matched_keywords": matched_keywords,
        "violations": violations,
        "relevance_score": round(relevance_score, 2)
    }


def _validate_row_context_logic(
    function: str, effect: str, failure_mode: str,
    cause: str, mechanism: str, prevention: str, detection: str
) -> dict:
    """행 전체 맥락 일관성 검증 [v2.0 신규]"""
    violations = []
    checks = {}

    # 1. B->C: 기능-영향 연관성
    bc_result = _validate_function_effect_logic(function, effect)
    checks["B_C"] = bc_result["status"]
    if bc_result["status"] == "fail":
        violations.extend([{**v, "check": "B->C"} for v in bc_result["violations"]])

    # 2. F->H: 원인-예방 연관성
    fh_result = _check_keyword_relevance(
        cause, prevention, CAUSE_PREVENTION_MAP,
        "F->H", "원인", "예방대책"
    )
    checks["F_H"] = fh_result["status"]
    if fh_result["status"] == "fail":
        violations.extend([{**v, "check": "F->H"} for v in fh_result["violations"]])

    # 3. E->J: 형태-검출 연관성
    ej_result = _check_keyword_relevance(
        failure_mode, detection, MODE_DETECTION_MAP,
        "E->J", "형태", "검출대책"
    )
    checks["E_J"] = ej_result["status"]
    if ej_result["status"] == "fail":
        violations.extend([{**v, "check": "E->J"} for v in ej_result["violations"]])

    # 4. F->G: 원인-메커니즘 도메인 일치
    fg_result = _validate_cause_mechanism_logic(cause, mechanism)
    checks["F_G"] = fg_result["status"]
    if fg_result["status"] == "fail":
        violations.extend([{**v, "check": "F->G"} for v in fg_result["violations"]])

    # 5. G->E: 메커니즘 결과가 형태와 일치
    # 동의어 매핑 (메커니즘 결과 용어 -> 형태 용어 양방향 호환)
    GE_SYNONYMS = {
        "파단": ["단선", "끊어짐", "파손", "절단"],
        "단선": ["파단", "끊어짐", "파손", "절단"],
        "이완": ["풀림", "탈락"],
        "풀림": ["이완", "탈락"],
        "탈락": ["이완", "풀림", "분리"],
        "손상": ["파손", "열화", "열손상", "크랙"],
        "크랙": ["균열", "손상"],
        "균열": ["크랙", "손상"],
        "누유": ["누설", "유출"],
        "누설": ["누유", "유출"],
        "변형": ["뒤틀림", "휨"],
        "뒤틀림": ["변형", "휨"],
        "절연파괴": ["단락", "지락", "방전"],
        "단락": ["절연파괴", "지락"],
    }
    # [v2.4] -> 와 unicode arrow 모두 지원
    import re as _re
    mech_parts = _re.split(r"->|\u2192", mechanism)
    if len(mech_parts) >= 2:
        mech_result_part = mech_parts[-1].strip()
        mode_clean = failure_mode
        for tag in REQUIRED_TAGS:
            mode_clean = mode_clean.replace(tag, "").strip()

        ge_match = False
        mode_words = [w for w in mode_clean.split() if len(w) >= 2]
        for word in mode_words:
            if word in mech_result_part:
                ge_match = True
                break
            # 동의어 확인
            for mech_word in [w for w in mech_result_part.split() if len(w) >= 2]:
                synonyms = GE_SYNONYMS.get(mech_word, [])
                if word in synonyms:
                    ge_match = True
                    break
                # 역방향도 확인
                word_synonyms = GE_SYNONYMS.get(word, [])
                if mech_word in word_synonyms:
                    ge_match = True
                    break
            if ge_match:
                break

        if not ge_match and mode_words:
            violations.append({
                "type": "MECHANISM_RESULT_MISMATCH",
                "check": "G->E",
                "mechanism_result": mech_result_part,
                "failure_mode": mode_clean,
                "message": f"메커니즘 결과('{mech_result_part}')가 형태('{mode_clean}')와 불일치"
            })
            checks["G_E"] = "fail"
        else:
            checks["G_E"] = "pass"
    else:
        checks["G_E"] = "skip"

    # 6. C->E: 영향-형태 연관성
    ce_result = _check_keyword_relevance(
        effect, failure_mode, EFFECT_MODE_MAP,
        "C->E", "영향", "형태"
    )
    checks["C_E"] = ce_result["status"]
    if ce_result["status"] == "fail":
        violations.extend([{**v, "check": "C->E"} for v in ce_result["violations"]])

    # 7. E->F: 형태-원인 인과관계 (causal_chain 활용)
    ef_result = _validate_causal_chain_logic(failure_mode, cause)
    checks["E_F"] = ef_result["status"]
    if ef_result["status"] == "fail":
        violations.extend([{**v, "check": "E->F"} for v in ef_result["violations"]])

    # context_score 계산
    total_checks = len([v for v in checks.values() if v != "skip"])
    passed_checks = len([v for v in checks.values() if v == "pass"])
    context_score = passed_checks / max(1, total_checks)

    return {
        "status": "pass" if not violations else "fail",
        "checks": checks,
        "violations": violations,
        "context_score": round(context_score, 2),
        "violation_count": len(violations)
    }


# ============================================================
# 검증 도구 - MCP 래퍼 (기존 8개 + 신규 3개 = 11개)
# ============================================================

@mcp.tool
def fmea_validate_failure_mode(failure_mode: str) -> str:
    """
    E열 (고장형태) 금지어 및 태그 검증

    [BLOCKING] 검증 실패 시 FMEA 항목 생성 불가!

    검증 규칙:
    1. 태그 필수: 부족:/과도:/유해: 중 하나
    2. 메커니즘 금지: 피로, 응력집중, 크리프 등 -> G열로 이동
    3. 측정값 금지: ~증가, ~저하 등 -> G열로 이동
    4. 미래결과 금지: 소음, 진동, 트립 등 -> C열로 이동

    Args:
        failure_mode: 검증할 고장형태 문자열 (예: '부족: 층간단락')

    Returns:
        JSON: {status, input, violations, suggestions}
    """
    result = _validate_failure_mode_logic(failure_mode)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
def fmea_validate_effect(effect: str) -> str:
    """
    C열 (고장영향) 검증

    검증 규칙:
    1. 미래 시점 확인 (앞으로 고객에게 영향?)
    2. 물리적 상태 금지: 크랙, 변형, 단락 등 -> E열로 이동

    Args:
        effect: 검증할 고장영향 문자열

    Returns:
        JSON: {status, violations, suggestions}
    """
    result = _validate_effect_logic(effect)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
def fmea_validate_cause(cause: str) -> str:
    """
    F열 (고장원인) 라이프사이클 태그 검증

    검증 규칙:
    1. 태그 필수: 설계:/재료:/제작:/시험: 중 하나
    2. 과거 시점 확인 (과거에 잘못된 것?)

    Args:
        cause: 검증할 고장원인 문자열

    Returns:
        JSON: {status, violations, suggestions}
    """
    result = _validate_cause_logic(cause)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
def fmea_validate_mechanism(mechanism: str) -> str:
    """
    G열 (고장메커니즘) 화살표 형식 검증

    검증 규칙:
    1. 화살표 2개 이상: 원인 -> 과정 -> 결과
    2. 시간순 전개 확인

    Args:
        mechanism: 검증할 고장메커니즘 문자열

    Returns:
        JSON: {status, arrow_count, violations}
    """
    result = _validate_mechanism_logic(mechanism)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
def fmea_validate_prevention(prevention: str, cause: Optional[str] = None) -> str:
    """
    H열 (현재예방대책) 다중줄/기준값 검증

    [v2.0] cause 전달 시 원인-예방 맥락 연관성도 검증 (WARNING)

    검증 규칙:
    1. 최소 4줄 이상 (라이프사이클별 1개 이상)
    2. 기준값 포함 권장
    3. [v2.0] cause 맥락: 원인 키워드와 예방 키워드 연관성

    Args:
        prevention: 검증할 현재예방대책 문자열 (줄바꿈으로 구분)
        cause: (선택) 고장원인 (F열) - 맥락 검증용

    Returns:
        JSON: {status, line_count, violations, warnings?}
    """
    result = _validate_prevention_logic(prevention, cause=cause)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
def fmea_validate_detection(detection: str, failure_mode: Optional[str] = None) -> str:
    """
    J열 (현재검출대책) 다중줄/합격기준 검증

    [v2.0] failure_mode 전달 시 형태-검출 맥락 연관성도 검증 (WARNING)

    검증 규칙:
    1. 최소 4줄 이상 (라이프사이클별 1개 이상)
    2. 합격기준 포함 권장
    3. [v2.0] failure_mode 맥락: 형태 키워드와 검출 키워드 연관성

    Args:
        detection: 검증할 현재검출대책 문자열 (줄바꿈으로 구분)
        failure_mode: (선택) 고장형태 (E열) - 맥락 검증용

    Returns:
        JSON: {status, line_count, violations, warnings?}
    """
    result = _validate_detection_logic(detection, failure_mode=failure_mode)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
def fmea_validate_causal_chain(failure_mode: str, cause: str) -> str:
    """
    E열(고장형태)과 F열(고장원인)의 인과관계 검증

    [BLOCKING] 논리적 인과관계 불성립 시 항목 생성 불가!

    검증 원리:
    - 층간단락/지락/절연파괴 = 절연 문제 -> 유효원인: 절연열화, 과전압
    - 턴수/전압비 오류 = 전기계산 문제 -> 유효결과: 전압비불일치

    Args:
        failure_mode: 고장형태 (E열)
        cause: 고장원인 (F열)

    Returns:
        JSON: {status, violations, reason}
    """
    result = _validate_causal_chain_logic(failure_mode, cause)
    return json.dumps(result, ensure_ascii=False, indent=2)


# ============================================================
# v2.0 신규 MCP 도구 (3개)
# ============================================================

@mcp.tool
def fmea_validate_cause_mechanism(cause: str, mechanism: str) -> str:
    """
    F열(고장원인)과 G열(고장메커니즘)의 도메인 일치 검증 [v2.0 신규]

    [BLOCKING] 원인과 메커니즘의 도메인이 불일치하면 항목 생성 불가!

    검증 규칙:
    1. 원인/메커니즘 도메인 분류 (전기/기계/열/화학/유체)
    2. 도메인 교차 검증 (같은 도메인인지)
    3. 라이프사이클 일관성 (원인 단계 = 메커니즘 단계)

    Args:
        cause: 고장원인 (F열) - 라이프사이클 태그 포함
        mechanism: 고장메커니즘 (G열) - 화살표 형식

    Returns:
        JSON: {status, cause_domains, mechanism_domains, violations}
    """
    result = _validate_cause_mechanism_logic(cause, mechanism)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
def fmea_validate_function_effect(function: str, effect: str) -> str:
    """
    B열(기능)과 C열(고장영향)의 연관성 검증 [v2.0 신규]

    검증 규칙:
    1. 기능 키워드 추출 (전류, 자속, 절연, 지지, 냉각 등)
    2. 영향 키워드 추출 (통전불가, 절연파괴, 과열 등)
    3. 키워드 매핑 테이블 기반 연관성 검증
    4. 연관성 없을 때 FAIL 반환

    Args:
        function: 기능 (B열)
        effect: 고장영향 (C열)

    Returns:
        JSON: {status, matched_keywords, violations, relevance_score}
    """
    result = _validate_function_effect_logic(function, effect)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
def fmea_validate_row_context(
    function: str, effect: str, failure_mode: str,
    cause: str, mechanism: str, prevention: str, detection: str
) -> str:
    """
    행 전체 맥락 일관성 검증 [v2.0 신규]

    [BLOCKING] 개별 컬럼이 모두 PASS여도 행 전체 맥락이 불일치하면 FAIL!

    검증 항목 (5개 체크):
    1. B->C: 기능 키워드와 영향 연관성
    2. F->H: 원인 키워드와 예방대책 연관성
    3. E->J: 형태 키워드와 검출방법 연관성
    4. F->G: 원인이 메커니즘 시작점인지 (도메인 일치)
    5. G->E: 메커니즘 결과가 형태와 일치하는지

    Args:
        function: 기능 (B열)
        effect: 고장영향 (C열)
        failure_mode: 고장형태 (E열)
        cause: 고장원인 (F열)
        mechanism: 고장메커니즘 (G열)
        prevention: 현재예방대책 (H열)
        detection: 현재검출대책 (J열)

    Returns:
        JSON: {status, checks, violations, context_score}
    """
    result = _validate_row_context_logic(
        function, effect, failure_mode,
        cause, mechanism, prevention, detection
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


# ============================================================
# 배치 검증 도구
# ============================================================

@mcp.tool
def fmea_validate_batch(json_content: str) -> str:
    """
    배치 JSON 전체 검증

    [v2.0] 행 단위 맥락 검증 추가 (context_violations)

    검증 항목:
    1. JSON 구조 유효성
    2. 모든 항목 개별 검증 (E/C/F/G/H/J열)
    3. [v2.0] 행 단위 맥락 검증 (B->C, F->H, E->J, F->G, G->E)

    Args:
        json_content: 검증할 JSON 문자열 또는 파일 경로

    Returns:
        JSON: {status, total_items, passed, failed, details, context_violations?}
    """
    try:
        # JSON 파싱 시도
        if json_content.strip().startswith("{") or json_content.strip().startswith("["):
            data = json.loads(json_content)
        else:
            # 파일 경로로 처리
            with open(json_content, 'r', encoding='utf-8') as f:
                data = json.load(f)
    except json.JSONDecodeError as e:
        return json.dumps({
            "status": "fail",
            "error": f"JSON 파싱 오류: {str(e)}"
        }, ensure_ascii=False)
    except FileNotFoundError:
        return json.dumps({
            "status": "fail",
            "error": f"파일 미존재: {json_content}"
        }, ensure_ascii=False)

    # 항목 검증
    items = data if isinstance(data, list) else data.get("items", [data])
    total = len(items)
    passed = 0
    failed = 0
    details = []
    context_violations = []

    for i, item in enumerate(items):
        item_errors = []

        # E열 검증
        fm = item.get("failure_mode") or item.get("고장형태", "")
        if fm:
            fm_result = _validate_failure_mode_logic(fm)
            if fm_result["status"] == "fail":
                item_errors.extend(fm_result["violations"])

        # F열 검증
        cause = item.get("cause") or item.get("고장원인", "")
        if cause:
            cause_result = _validate_cause_logic(cause)
            if cause_result["status"] == "fail":
                item_errors.extend(cause_result["violations"])

        # G열 검증
        mech = item.get("mechanism") or item.get("고장메커니즘", "")
        if mech:
            mech_result = _validate_mechanism_logic(mech)
            if mech_result["status"] == "fail":
                item_errors.extend(mech_result["violations"])

        # v2.0: 행 맥락 검증
        func = item.get("function") or item.get("기능", "")
        effect = item.get("effect") or item.get("고장영향", "")
        prev = item.get("prevention") or item.get("현재예방대책", "")
        det = item.get("detection") or item.get("현재검출대책", "")

        if func and effect and fm and cause and mech and prev and det:
            ctx_result = _validate_row_context_logic(
                func, effect, fm, cause, mech, prev, det
            )
            if ctx_result["status"] == "fail":
                context_violations.append({
                    "index": i,
                    "context_score": ctx_result["context_score"],
                    "violations": ctx_result["violations"]
                })

        if item_errors:
            failed += 1
            details.append({
                "index": i,
                "errors": item_errors
            })
        else:
            passed += 1

    has_context_issues = len(context_violations) > 0
    result = {
        "status": "pass" if (failed == 0 and not has_context_issues) else "fail",
        "total_items": total,
        "passed": passed,
        "failed": failed,
        "details": details if failed > 0 else []
    }

    if context_violations:
        result["context_violations"] = context_violations

    return json.dumps(result, ensure_ascii=False, indent=2)


# ============================================================
# 환각 방지 도구 (2개)
# ============================================================

@mcp.tool
def fmea_register_read(file_path: str, content_hash: str) -> str:
    """
    파일 Read 완료 등록 + 해시 검증

    [BLOCKING] Claude가 파일 Read 후 반드시 호출!

    워크플로우:
    1. Claude: Read(file_path)
    2. Claude: content_hash = SHA256(파일내용 앞 1000자)[:16]
    3. Claude: fmea_register_read(file_path, content_hash)
    4. MCP: 파일 직접 읽어 해시 대조
    5. 일치 -> 등록 완료
    6. 불일치 -> 오류 (다시 Read 필요)

    Args:
        file_path: 읽은 파일의 절대 경로
        content_hash: 파일 내용의 SHA256 해시 앞 16자

    Returns:
        JSON: {status, file, message}
    """
    global _read_files

    try:
        # MCP 서버가 직접 파일 읽기
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(1000)  # 앞 1000자만
        actual_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    except FileNotFoundError:
        return json.dumps({
            "status": "ERROR",
            "message": f"파일 미존재: {file_path}"
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "status": "ERROR",
            "message": f"파일 읽기 오류: {str(e)}"
        }, ensure_ascii=False)

    # 해시 비교 (앞 16자만 비교)
    if actual_hash != content_hash[:16]:
        return json.dumps({
            "status": "MISMATCH",
            "message": "해시 불일치! 파일을 다시 Read하세요.",
            "expected": content_hash[:16],
            "actual": actual_hash,
            "file": file_path
        }, ensure_ascii=False)

    # 등록
    _read_files[file_path] = actual_hash
    return json.dumps({
        "status": "REGISTERED",
        "file": file_path,
        "hash": actual_hash,
        "total_registered": len(_read_files)
    }, ensure_ascii=False)


@mcp.tool
def fmea_check_read_status(required_patterns: Optional[str] = None) -> str:
    """
    필수 파일 Read 완료 상태 확인

    Args:
        required_patterns: 필수 파일 패턴 (쉼표 구분, 예: "CHECK SHEET,Work Flow")

    Returns:
        JSON: {
            all_complete: bool,
            registered_count: int,
            registered_files: [...],
            missing_patterns: [...] (패턴 지정 시)
        }
    """
    global _read_files

    result = {
        "registered_count": len(_read_files),
        "registered_files": list(_read_files.keys())
    }

    if required_patterns:
        patterns = [p.strip() for p in required_patterns.split(",")]
        missing = []

        for pattern in patterns:
            found = any(pattern in f for f in _read_files.keys())
            if not found:
                missing.append(pattern)

        result["all_complete"] = len(missing) == 0
        result["missing_patterns"] = missing
    else:
        result["all_complete"] = len(_read_files) > 0

    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
def fmea_create_item(
    failure_mode: str,
    cause: str,
    mechanism: str,
    effect: str,
    prevention: str,
    detection: str,
    function: Optional[str] = None,
    prevention_source: Optional[str] = None,
    detection_source: Optional[str] = None
) -> str:
    """
    FMEA 항목 생성 (환각 방지 + 맥락 검증 포함)

    [BLOCKING] H/J열 출처 파일이 Read 등록되지 않으면 거부!
    [v2.0] function 전달 시 행 맥락 검증도 수행!

    검증 순서:
    1. 출처 파일 Read 등록 확인 (prevention_source, detection_source)
    2. E열 (failure_mode) 검증
    3. F열 (cause) 검증
    4. E-F 인과관계 검증
    5. G열 (mechanism) 검증
    6. C열 (effect) 검증
    7. H열 (prevention) 검증
    8. J열 (detection) 검증
    9. [v2.0] 행 전체 맥락 검증 (function 전달 시)

    Args:
        failure_mode: 고장형태 (E열) - 필수 태그: 부족:/과도:/유해:
        cause: 고장원인 (F열) - 필수 태그: 설계:/재료:/제작:/시험:
        mechanism: 고장메커니즘 (G열) - 화살표 2개 이상
        effect: 고장영향 (C열) - 미래 시점 영향
        prevention: 현재예방대책 (H열) - 4줄 이상
        detection: 현재검출대책 (J열) - 4줄 이상
        function: (선택) 기능 (B열) - 행 맥락 검증용 [v2.0]
        prevention_source: H열 출처 파일 경로 (환각방지용)
        detection_source: J열 출처 파일 경로 (환각방지용)

    Returns:
        JSON: {status, item, validation_results} 또는 {status: BLOCKED, reason}
    """
    global _read_files

    errors = []
    warnings = []

    # 1. 출처 파일 Read 등록 확인 (환각 방지)
    if prevention_source:
        if prevention_source not in _read_files:
            errors.append({
                "type": "SOURCE_NOT_READ",
                "column": "H",
                "source": prevention_source,
                "message": f"H열 출처 파일 미등록: {prevention_source}. fmea_register_read() 먼저 호출 필요!"
            })
    else:
        warnings.append("H열 출처 파일 미지정 - 환각 위험!")

    if detection_source:
        if detection_source not in _read_files:
            errors.append({
                "type": "SOURCE_NOT_READ",
                "column": "J",
                "source": detection_source,
                "message": f"J열 출처 파일 미등록: {detection_source}. fmea_register_read() 먼저 호출 필요!"
            })
    else:
        warnings.append("J열 출처 파일 미지정 - 환각 위험!")

    # 출처 미등록 시 즉시 거부
    if errors:
        return json.dumps({
            "status": "BLOCKED",
            "reason": "출처 파일 Read 미등록",
            "errors": errors,
            "action_required": "1. Read(출처파일) 2. fmea_register_read(경로, 해시) 3. 다시 시도"
        }, ensure_ascii=False, indent=2)

    # 2-8. 각 컬럼 검증
    validation_results = {}

    # E열 검증
    fm_result = _validate_failure_mode_logic(failure_mode)
    validation_results["E_failure_mode"] = fm_result
    if fm_result["status"] == "fail":
        errors.extend([{"column": "E", **v} for v in fm_result["violations"]])

    # F열 검증
    cause_result = _validate_cause_logic(cause)
    validation_results["F_cause"] = cause_result
    if cause_result["status"] == "fail":
        errors.extend([{"column": "F", **v} for v in cause_result["violations"]])

    # E-F 인과관계 검증
    causal_result = _validate_causal_chain_logic(failure_mode, cause)
    validation_results["EF_causal_chain"] = causal_result
    if causal_result["status"] == "fail":
        errors.extend([{"column": "E-F", **v} for v in causal_result["violations"]])

    # G열 검증
    mech_result = _validate_mechanism_logic(mechanism)
    validation_results["G_mechanism"] = mech_result
    if mech_result["status"] == "fail":
        errors.extend([{"column": "G", **v} for v in mech_result["violations"]])

    # C열 검증
    effect_result = _validate_effect_logic(effect)
    validation_results["C_effect"] = effect_result
    if effect_result["status"] == "fail":
        errors.extend([{"column": "C", **v} for v in effect_result["violations"]])

    # H열 검증 (v2.0: cause 맥락 포함)
    prev_result = _validate_prevention_logic(prevention, cause=cause)
    validation_results["H_prevention"] = prev_result
    if prev_result["status"] == "fail":
        errors.extend([{"column": "H", **v} for v in prev_result["violations"]])
    if prev_result.get("warnings"):
        warnings.extend([w["message"] for w in prev_result["warnings"]])

    # J열 검증 (v2.0: failure_mode 맥락 포함)
    det_result = _validate_detection_logic(detection, failure_mode=failure_mode)
    validation_results["J_detection"] = det_result
    if det_result["status"] == "fail":
        errors.extend([{"column": "J", **v} for v in det_result["violations"]])
    if det_result.get("warnings"):
        warnings.extend([w["message"] for w in det_result["warnings"]])

    # 9. [v2.0] 행 전체 맥락 검증
    if function:
        ctx_result = _validate_row_context_logic(
            function, effect, failure_mode,
            cause, mechanism, prevention, detection
        )
        validation_results["row_context"] = ctx_result
        if ctx_result["status"] == "fail":
            errors.extend([{"column": "ROW", **v} for v in ctx_result["violations"]])

    # 검증 실패 시 거부
    if errors:
        return json.dumps({
            "status": "VALIDATION_FAILED",
            "error_count": len(errors),
            "errors": errors,
            "validation_results": validation_results
        }, ensure_ascii=False, indent=2)

    # 검증 통과 - 항목 생성
    item = {
        "failure_mode": failure_mode,
        "cause": cause,
        "mechanism": mechanism,
        "effect": effect,
        "prevention": prevention,
        "detection": detection,
        "prevention_source": prevention_source,
        "detection_source": detection_source
    }
    if function:
        item["function"] = function

    return json.dumps({
        "status": "CREATED",
        "item": item,
        "validation_results": validation_results,
        "warnings": warnings if warnings else None
    }, ensure_ascii=False, indent=2)


# ============================================================
# 조회 도구
# ============================================================

@mcp.tool
def fmea_get_forbidden_words() -> str:
    """
    E열 금지어 목록 조회

    Returns:
        JSON: {mechanisms, measurements, future_results, required_tags}
    """
    return json.dumps({
        "mechanisms": FORBIDDEN_MECHANISMS,
        "measurements": FORBIDDEN_MEASUREMENTS,
        "future_results": FORBIDDEN_FUTURE_RESULTS,
        "required_tags": REQUIRED_TAGS,
        "lifecycle_tags": LIFECYCLE_TAGS
    }, ensure_ascii=False, indent=2)


@mcp.tool
def fmea_get_invalid_causal_combinations() -> str:
    """
    E->F 금지 인과관계 조합 조회

    Returns:
        JSON: {mode: [invalid_causes]}
    """
    return json.dumps(INVALID_CAUSAL_COMBINATIONS, ensure_ascii=False, indent=2)


# ============================================================
# 서버 실행
# ============================================================

if __name__ == "__main__":
    # stdio 전송으로 실행
    mcp.run(transport="stdio")
