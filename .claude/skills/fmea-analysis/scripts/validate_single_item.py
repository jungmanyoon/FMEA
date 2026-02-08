#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FMEA 단일 항목 사전 검증 스크립트

목적: FMEA 항목 생성 중 즉시 검증하여 반복 수정 최소화
사용: python validate_single_item.py --item '{"고장형태": "부족: 이완", ...}'
      python validate_single_item.py --json input.json --index 0

근본 원인 분석 결과:
- 프롬프트 copy.txt 분석: Excel 생성 시점 검증 -> 5-7회 반복 수정
- 해결: 항목 생성 중 즉시 검증으로 오류 조기 발견
"""

import json
import argparse
import sys
import os
from pathlib import Path

# 스킬 디렉토리 기준 경로
SKILL_DIR = Path(__file__).parent.parent
REFERENCES_DIR = SKILL_DIR / "references"


def load_failure_mode_ontology():
    """failure-mode-ontology.md에서 금지어 로드"""
    ontology_path = REFERENCES_DIR / "failure-mode-ontology.md"

    ontology = {
        "forbidden_patterns": [],
        "forbidden_exact": [],
        "mechanism_keywords": [],
        "required_tags": ["부족:", "과도:", "유해:"],
        "visible_phenomena": []
    }

    if not ontology_path.exists():
        print(f"[WARN] 온톨로지 파일 없음: {ontology_path}")
        # 기본 금지어 사용
        ontology["mechanism_keywords"] = [
            "피로", "응력집중", "크리프", "열화진행", "부식진행",
            "산화진행", "마모진행", "열피로", "기계피로", "열팽창",
            "열수축", "와전류", "히스테리시스"
        ]
        ontology["forbidden_exact"] = [
            "소음", "진동", "오작동", "동작불가", "트립", "정전",
            "체결력 부족", "고정력 부족", "압착력 부족", "클램핑력 부족"
        ]
        ontology["forbidden_patterns"] = ["증가", "저하", "상승", "감소"]
        return ontology

    current_section = None
    with open(ontology_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line.startswith("## SECTION:"):
                current_section = line.replace("## SECTION:", "").strip()
                continue

            if current_section == "FORBIDDEN_PATTERNS" and ":" in line:
                _, values = line.split(":", 1)
                ontology["forbidden_patterns"].extend([v.strip() for v in values.split(",")])

            elif current_section == "FORBIDDEN_EXACT" and ":" in line:
                _, values = line.split(":", 1)
                ontology["forbidden_exact"].extend([v.strip() for v in values.split(",")])

            elif current_section == "MECHANISM_KEYWORDS" and ":" in line and not line.startswith("|"):
                _, values = line.split(":", 1)
                ontology["mechanism_keywords"].extend([v.strip() for v in values.split(",")])

            elif current_section == "VISIBLE_PHENOMENA" and ":" in line:
                _, values = line.split(":", 1)
                ontology["visible_phenomena"].extend([v.strip() for v in values.split(",")])

    return ontology


def load_effect_ontology():
    """effect-ontology.md에서 C열 금지어 로드"""
    ontology_path = REFERENCES_DIR / "effect-ontology.md"

    ontology = {
        "forbidden_physical": [],
        "forbidden_results": []
    }

    if not ontology_path.exists():
        print(f"[WARN] C열 온톨로지 파일 없음: {ontology_path}")
        # 기본 금지어 사용
        ontology["forbidden_physical"] = [
            "이완", "탈락", "균열", "변형", "크랙", "부식", "누설",
            "파손", "마모", "변색", "산화", "단락", "층간단락"
        ]
        ontology["forbidden_results"] = [
            "FAT 불합격", "FAT불합격", "시험 불합격", "부적합",
            "조립불합격", "용접불합격", "외관불합격"
        ]
        return ontology

    current_section = None
    with open(ontology_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line.startswith("## SECTION:"):
                current_section = line.replace("## SECTION:", "").strip()
                continue

            if "FORBIDDEN_PHYSICAL" in str(current_section) and ":" in line:
                _, values = line.split(":", 1)
                ontology["forbidden_physical"].extend([v.strip() for v in values.split(",")])

            if "FORBIDDEN_RESULTS" in str(current_section) and ":" in line:
                _, values = line.split(":", 1)
                ontology["forbidden_results"].extend([v.strip() for v in values.split(",")])

    # 기본 금지어 추가 (파싱 실패 시 대비)
    if not ontology["forbidden_physical"]:
        ontology["forbidden_physical"] = [
            "이완", "탈락", "균열", "변형", "크랙", "부식", "누설"
        ]
    if not ontology["forbidden_results"]:
        ontology["forbidden_results"] = [
            "FAT 불합격", "불합격", "부적합"
        ]

    return ontology


def validate_failure_mode(value: str, ontology: dict) -> list:
    """E열 (고장형태) 검증"""
    errors = []

    if not value:
        errors.append("[BLOCKING] E열(고장형태) 비어있음")
        return errors

    # 1줄만 검증 (옵션 A 3줄 구조 지원)
    first_line = value.split("\n")[0].strip()

    # 필수 태그 검증
    has_tag = any(first_line.startswith(tag) for tag in ontology["required_tags"])
    if not has_tag:
        errors.append(f"[BLOCKING] E열 태그 누락! 필수: 부족:/과도:/유해: 중 하나로 시작")
        errors.append(f"  현재값: '{first_line}'")

    # 메커니즘 키워드 검증
    for keyword in ontology.get("mechanism_keywords", []):
        if keyword and keyword.strip() and keyword in value:
            errors.append(f"[BLOCKING] E열에 메커니즘 용어 '{keyword}' 금지! -> G열로 이동")

    # 금지 패턴 검증
    for pattern in ontology.get("forbidden_patterns", []):
        if pattern in value:
            errors.append(f"[BLOCKING] E열에 측정값 패턴 '{pattern}' 금지! (예: ~증가, ~저하)")

    # 금지 정확 매칭 검증
    for exact in ontology.get("forbidden_exact", []):
        if exact in value:
            errors.append(f"[BLOCKING] E열에 금지어 '{exact}' 발견! -> C열 또는 G열로 이동")

    return errors


def validate_failure_effect(value: str, ontology: dict) -> list:
    """C열 (고장영향) 검증"""
    errors = []

    if not value:
        errors.append("[BLOCKING] C열(고장영향) 비어있음")
        return errors

    # 물리적 상태 검증
    for physical in ontology.get("forbidden_physical", []):
        if physical in value:
            errors.append(f"[BLOCKING] C열에 물리적 상태 '{physical}' 금지! -> E열로 이동")

    # 검사/판정 결과 검증
    for result in ontology.get("forbidden_results", []):
        if result in value:
            errors.append(f"[BLOCKING] C열에 검사결과 '{result}' 금지! -> 기술적 영향으로 변경")

    return errors


def validate_mechanism(value: str) -> list:
    """G열 (고장메커니즘) 검증 - 화살표 체인 형식 필수"""
    errors = []

    if not value:
        errors.append("[BLOCKING] G열(고장메커니즘) 비어있음")
        return errors

    # 화살표 형식 필수 검증
    if "->" not in value and "→" not in value:
        errors.append(f"[BLOCKING] G열 형식 오류! 화살표 체인 필수: '원인 -> 과정 -> 결과'")
        errors.append(f"  현재값: '{value}'")
        errors.append(f"  예시: '절연 코팅 열화 -> 층간 단락 -> 와전류 증가'")

    # 단답형 금지어 (F열 원인이 잘못 들어간 경우)
    cause_keywords = [
        "설계 오류", "재료 불량", "조립 오차", "검증 누락", "가공 불량",
        "치수 오차", "용접 불량", "체결 불량", "인장 파괴", "피로 파괴"
    ]
    for keyword in cause_keywords:
        if value == keyword or value.strip() == keyword:
            errors.append(f"[BLOCKING] G열에 원인 용어 '{keyword}' 금지! -> F열로 이동")
            errors.append(f"  G열은 메커니즘 체인: '원인 상태 -> 물리적 과정 -> 결과 상태'")

    return errors


def validate_lifecycle_tag(value: str, column_name: str) -> list:
    """라이프사이클 태그 검증 (H열, J열)"""
    errors = []

    if not value:
        return errors  # 빈 값은 WARNING이지만 여기서는 skip

    required_tags = ["설계:", "재료:", "제작:", "시험:"]
    has_tag = any(value.startswith(tag) for tag in required_tags)

    if not has_tag:
        errors.append(f"[WARNING] {column_name}에 라이프사이클 태그 권장: 설계:/재료:/제작:/시험:")

    return errors


def validate_prevention_multiline(value: str) -> list:
    """H열 (현재예방대책) 멀티라인 + 기준값 검증 - CRITICAL-3 규칙"""
    errors = []

    if not value:
        errors.append("[BLOCKING] H열(현재예방대책) 비어있음")
        return errors

    lines = [line.strip() for line in value.split("\n") if line.strip()]

    # 1. 멀티라인 검증 (4줄 이상 필수)
    if len(lines) < 4:
        errors.append(f"[BLOCKING] H열 멀티라인 필수! 4줄 이상 필요 (현재: {len(lines)}줄)")
        errors.append("  형식: 설계/재료/제작/시험 4단계별 대책 + 세부항목")
        errors.append("  예시:")
        errors.append("    설계: 클램프 강도 설계 검토 (중신 CHECK SHEET)")
        errors.append("    - 허용응력 계산: 안전율 2.0 이상 (IEQT-T-C018)")
        errors.append("    재료: 클램프 자재 수입검사 (IEQT-T-R018)")
        errors.append("    - 재질증명서 확인: SS400 이상")

    # 2. 라이프사이클 4단계 중 최소 2개 포함 검증
    lifecycle_tags = ["설계:", "재료:", "제작:", "시험:"]
    found_tags = [tag for tag in lifecycle_tags if any(tag in line for line in lines)]
    if len(found_tags) < 2:
        errors.append(f"[BLOCKING] H열 라이프사이클 태그 부족! 4단계 중 2개 이상 필요")
        errors.append(f"  발견된 태그: {found_tags if found_tags else '없음'}")
        errors.append(f"  필수 태그: 설계:, 재료:, 제작:, 시험:")

    # 3. 기준값 존재 검증 (수치 + 단위)
    value_patterns = [
        r'\d+[\.,]?\d*\s*(N\.?m|kgf|MPa|kPa|bar|mm|cm|m|%|도|°C|이상|이하|이내)',
        r'안전율\s*\d', r'SS\d+', r'\d+\s*mm', r'\d+\s*%'
    ]
    import re
    has_value = any(re.search(pattern, value, re.IGNORECASE) for pattern in value_patterns)
    if not has_value:
        errors.append("[WARNING] H열 기준값 권장! 정량적 수치(안전율, mm, %, N.m 등) 포함 필요")

    # 4. 출처 존재 검증
    source_patterns = [r'\([A-Z\-0-9]+', r'CHECK SHEET', r'IEQT', r'SS\d+']
    has_source = any(re.search(pattern, value, re.IGNORECASE) for pattern in source_patterns)
    if not has_source:
        errors.append("[WARNING] H열 출처 권장! (IEQT-T-W030, CHECK SHEET 등) 포함 필요")

    return errors


def validate_detection_multiline(value: str) -> list:
    """J열 (현재검출대책) 멀티라인 + 합격기준 검증 - CRITICAL-3 규칙"""
    errors = []

    if not value:
        errors.append("[BLOCKING] J열(현재검출대책) 비어있음")
        return errors

    lines = [line.strip() for line in value.split("\n") if line.strip()]

    # 1. 멀티라인 검증 (4줄 이상 필수)
    if len(lines) < 4:
        errors.append(f"[BLOCKING] J열 멀티라인 필수! 4줄 이상 필요 (현재: {len(lines)}줄)")
        errors.append("  형식: 설계/재료/제작/시험 4단계별 검출방법 + 합격기준")
        errors.append("  예시:")
        errors.append("    설계: 도면 승인 (설계팀)")
        errors.append("    - 클램프 강도 검토: 계산서 첨부 필수")
        errors.append("    제작: 용접 후 육안검사 (생산팀)")
        errors.append("    - 비드 외관: 크랙/언더컷 없음")

    # 2. 라이프사이클 4단계 중 최소 2개 포함 검증
    lifecycle_tags = ["설계:", "재료:", "제작:", "시험:"]
    found_tags = [tag for tag in lifecycle_tags if any(tag in line for line in lines)]
    if len(found_tags) < 2:
        errors.append(f"[BLOCKING] J열 라이프사이클 태그 부족! 4단계 중 2개 이상 필요")
        errors.append(f"  발견된 태그: {found_tags if found_tags else '없음'}")
        errors.append(f"  필수 태그: 설계:, 재료:, 제작:, 시험:")

    # 3. 합격기준 존재 검증 (수치 또는 합격/불합격 표현)
    import re
    criteria_patterns = [
        r'\d+[\.,]?\d*\s*(mm|%|이상|이하|이내|미만)',
        r'합격', r'불합격', r'없음', r'확인', r'검토', r'필수'
    ]
    has_criteria = any(re.search(pattern, value, re.IGNORECASE) for pattern in criteria_patterns)
    if not has_criteria:
        errors.append("[WARNING] J열 합격기준 권장! (크랙 없음, 2mm 이하 등) 포함 필요")

    return errors


def validate_diamond_structure(items: list) -> list:
    """다이아몬드 구조 검증 (형태당 원인 2개 이상)"""
    errors = []

    # 기능-고장형태별 원인 수 집계
    function_mode_causes = {}

    for item in items:
        func = item.get("기능", "")
        mode = item.get("고장형태", "")
        key = f"{func}|{mode}"

        if key not in function_mode_causes:
            function_mode_causes[key] = []
        function_mode_causes[key].append(item.get("고장원인", ""))

    # 원인 2개 미만 검출
    for key, causes in function_mode_causes.items():
        if len(causes) < 2:
            func, mode = key.split("|", 1)
            errors.append(f"[BLOCKING] 다이아몬드 구조 위반! 형태당 원인 2개 이상 필요")
            errors.append(f"  기능: '{func[:30]}...'")
            errors.append(f"  고장형태: '{mode[:30]}...'")
            errors.append(f"  현재 원인: {len(causes)}개")

    return errors


def validate_single_item(item: dict) -> dict:
    """단일 FMEA 항목 검증"""
    fm_ontology = load_failure_mode_ontology()
    effect_ontology = load_effect_ontology()

    result = {
        "valid": True,
        "errors": [],
        "warnings": []
    }

    # E열 검증
    e_errors = validate_failure_mode(item.get("고장형태", ""), fm_ontology)
    result["errors"].extend(e_errors)

    # C열 검증
    c_errors = validate_failure_effect(item.get("고장영향", ""), effect_ontology)
    result["errors"].extend(c_errors)

    # G열 검증 (고장메커니즘 - 화살표 체인 형식)
    g_errors = validate_mechanism(item.get("고장메커니즘", ""))
    result["errors"].extend(g_errors)

    # H열 검증 (멀티라인 + 기준값 - CRITICAL-3)
    h_errors = validate_prevention_multiline(item.get("현재예방대책", ""))
    for err in h_errors:
        if "[BLOCKING]" in err:
            result["errors"].append(err)
        else:
            result["warnings"].append(err)

    # J열 검증 (멀티라인 + 합격기준 - CRITICAL-3)
    j_errors = validate_detection_multiline(item.get("현재검출대책", ""))
    for err in j_errors:
        if "[BLOCKING]" in err:
            result["errors"].append(err)
        else:
            result["warnings"].append(err)

    # F열 검증 (라이프사이클 태그)
    f_warnings = validate_lifecycle_tag(item.get("고장원인", ""), "F열(고장원인)")
    result["warnings"].extend(f_warnings)

    # 유효성 판정
    result["valid"] = len(result["errors"]) == 0

    return result


def validate_json_file(json_path: str, index: int = None) -> dict:
    """JSON 파일에서 항목 검증"""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # fmea_data 구조 처리
    items = data.get("fmea_data", data.get("items", data))
    if isinstance(items, dict):
        items = items.get("items", [items])

    if index is not None:
        if 0 <= index < len(items):
            return validate_single_item(items[index])
        else:
            return {"valid": False, "errors": [f"인덱스 {index}가 범위를 벗어남 (총 {len(items)}개)"], "warnings": []}

    # 전체 검증
    all_errors = []
    all_warnings = []

    for i, item in enumerate(items):
        result = validate_single_item(item)
        if result["errors"]:
            all_errors.append(f"\n[항목 {i+1}]")
            all_errors.extend(result["errors"])
        if result["warnings"]:
            all_warnings.append(f"\n[항목 {i+1}]")
            all_warnings.extend(result["warnings"])

    # 다이아몬드 구조 검증
    diamond_errors = validate_diamond_structure(items)
    if diamond_errors:
        all_errors.append("\n[다이아몬드 구조]")
        all_errors.extend(diamond_errors)

    return {
        "valid": len(all_errors) == 0,
        "errors": all_errors,
        "warnings": all_warnings,
        "total_items": len(items)
    }


def main():
    parser = argparse.ArgumentParser(description="FMEA 단일 항목 사전 검증")
    parser.add_argument("--item", type=str, help="JSON 형식 단일 항목")
    parser.add_argument("--json", type=str, help="JSON 파일 경로")
    parser.add_argument("--index", type=int, help="검증할 항목 인덱스")
    parser.add_argument("--quiet", action="store_true", help="경고 숨기기")

    args = parser.parse_args()

    if args.item:
        item = json.loads(args.item)
        result = validate_single_item(item)
    elif args.json:
        result = validate_json_file(args.json, args.index)
    else:
        parser.print_help()
        sys.exit(1)

    # 결과 출력
    print("=" * 60)
    if result["valid"]:
        print("[OK] 검증 통과!")
    else:
        print("[X] 검증 실패!")
    print("=" * 60)

    if result["errors"]:
        print("\n[ERRORS]")
        for error in result["errors"]:
            print(f"  {error}")

    if result["warnings"] and not args.quiet:
        print("\n[WARNINGS]")
        for warning in result["warnings"]:
            print(f"  {warning}")

    if "total_items" in result:
        print(f"\n총 항목 수: {result['total_items']}")

    print("=" * 60)

    # 종료 코드
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
