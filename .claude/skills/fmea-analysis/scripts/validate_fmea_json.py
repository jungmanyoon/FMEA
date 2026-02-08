#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FMEA JSON 사전 검증 스크립트

목적: GATE 3 전에 JSON 데이터의 모든 컬럼 형식을 검증
용도: Claude의 "자가 검증" 대신 스크립트 기반 검증 수행

사용법:
    python validate_fmea_json.py input_data.json

반환:
    - 통과: exit code 0 + "GATE 3 PASS" 메시지
    - 실패: exit code 1 + 위반 항목 목록
"""

import sys
import json
import os
import re
from pathlib import Path

# Windows cp949 인코딩 문제 해결
from encoding_utils import setup_encoding
setup_encoding()

# 기존 검증 모듈 재사용
from validate_failure_mode import validate_failure_mode, validate_tag_format
from validate_failure_effect import validate_failure_effect, validate_physical_in_effect
from validate_single_item import (
    validate_mechanism,
    validate_prevention_multiline,
    validate_detection_multiline
)
from validate_causal_chain import validate_mode_cause, validate_cause_mechanism


def validate_column_e(items):
    """E열 (고장형태) 검증: 태그 + 메커니즘 제외"""
    violations = []
    for i, item in enumerate(items, 1):
        failure_mode = item.get('고장형태', '')

        # 태그 검증 - validate_tag_format()은 Tuple[bool, str] 반환
        is_valid_tag, reason_tag = validate_tag_format(failure_mode)
        if not is_valid_tag:
            violations.append(f"  - 항목 {i}: E열 태그 누락 - \"{failure_mode[:30]}...\"")

        # 메커니즘 금지어 검증 - validate_failure_mode()도 Tuple[bool, str] 반환
        is_valid_mode, reason_mode = validate_failure_mode(failure_mode)
        if not is_valid_mode:
            violations.append(f"  - 항목 {i}: E열 {reason_mode}")

    return violations


def validate_column_c(items, forbidden_physical=None):
    """C열 (고장영향) 검증: 물리적 상태 제외"""
    violations = []

    # forbidden_physical이 없으면 온톨로지에서 로드
    if forbidden_physical is None:
        from validate_failure_effect import load_effect_ontology
        ontology = load_effect_ontology()
        forbidden_physical = ontology.get('forbidden_physical', [])

    for i, item in enumerate(items, 1):
        effect = item.get('고장영향', '')

        # 물리적 상태 검증 - 올바른 함수 시그니처 사용
        is_valid, reason = validate_physical_in_effect(effect, forbidden_physical)
        if not is_valid:
            violations.append(f"  - 항목 {i}: C열 물리적 상태 포함 - \"{effect[:40]}...\" -> {reason}")

        # 검사/판정 결과 검증 - validate_failure_effect()는 Tuple[bool, str] 반환
        is_valid_effect, reason_effect = validate_failure_effect(effect)
        if not is_valid_effect:
            violations.append(f"  - 항목 {i}: C열 {reason_effect}")

    return violations


def validate_column_f(items):
    """F열 (고장원인) 검증: 라이프사이클 태그 필수"""
    violations = []
    lifecycle_tags = ['설계:', '재료:', '제작:', '시험:']

    for i, item in enumerate(items, 1):
        cause = item.get('고장원인', '')
        has_tag = any(tag in cause for tag in lifecycle_tags)
        if not has_tag:
            violations.append(f"  - 항목 {i}: F열 라이프사이클 태그 누락 - \"{cause[:30]}...\"")

    return violations


def validate_column_g(items):
    """G열 (고장메커니즘) 검증: 화살표 2개 이상"""
    violations = []
    for i, item in enumerate(items, 1):
        mechanism = item.get('고장메커니즘', '')
        # validate_mechanism()은 에러 리스트 반환
        errors = validate_mechanism(mechanism)
        if errors:
            for err in errors:
                violations.append(f"  - 항목 {i}: G열 {err}")

    return violations


def validate_column_h(items):
    """H열 (현재예방대책) 검증: 4줄 이상 + 기준값 + 태그 2개 이상"""
    violations = []
    for i, item in enumerate(items, 1):
        prevention = item.get('현재예방대책', '')
        # validate_prevention_multiline()은 에러 리스트 반환
        errors = validate_prevention_multiline(prevention)
        if errors:
            for err in errors:
                violations.append(f"  - 항목 {i}: H열 {err}")

    return violations


def validate_column_j(items):
    """J열 (현재검출대책) 검증: 4줄 이상 + 합격기준 + 태그 2개 이상"""
    violations = []
    for i, item in enumerate(items, 1):
        detection = item.get('현재검출대책', '')
        # validate_detection_multiline()은 에러 리스트 반환
        errors = validate_detection_multiline(detection)
        if errors:
            for err in errors:
                violations.append(f"  - 항목 {i}: J열 {err}")

    return violations


def validate_causal_relationships(items):
    """E->F 인과관계 체인 검증 [BLOCKING]

    causal-chain-ontology.md의 INVALID_COMBINATIONS 규칙 적용
    예: 층간단락 <- 턴수오류 = 인과관계 불성립 -> FAIL
    """
    violations = []
    for i, item in enumerate(items, 1):
        mode = item.get('고장형태', '')
        cause = item.get('고장원인', '')

        if mode and cause:
            # E->F 검증: 고장형태와 원인의 인과관계 확인
            is_valid, reason = validate_mode_cause(mode, cause)
            if not is_valid:
                violations.append(f"  - 항목 {i}: E->F 인과관계 오류 - {reason}")

    return violations


def validate_lifecycle_balance(items):
    """F열 라이프사이클 비율 검증 [WARNING]

    각 단계 비율: 10% 이상 권장, 0%는 BLOCKING
    목표: 설계(15-25%), 재료(20-30%), 제작(25-35%), 시험(15-25%)
    """
    stage_count = {'설계': 0, '재료': 0, '제작': 0, '시험': 0}

    for item in items:
        cause = item.get('고장원인', '')
        for stage in stage_count.keys():
            if cause.startswith(f'{stage}:'):
                stage_count[stage] += 1
                break

    total = sum(stage_count.values())
    if total == 0:
        return {'valid': False, 'violations': ['원인 데이터 없음'], 'stage_count': stage_count}

    violations = []
    warnings = []

    for stage, count in stage_count.items():
        ratio = (count / total) * 100
        if ratio == 0:
            violations.append(f"[BLOCKING] {stage}: 0% (최소 1개 필수)")
        elif ratio < 10:
            warnings.append(f"[WARNING] {stage}: {ratio:.1f}% (10% 미만 - 추가 검토 권장)")
        elif ratio > 50:
            warnings.append(f"[WARNING] {stage}: {ratio:.1f}% (50% 초과 - 과집중)")

    return {
        'valid': len(violations) == 0,
        'violations': violations,
        'warnings': warnings,
        'stage_count': stage_count,
        'total': total
    }


def validate_diamond_preview(items):
    """다이아몬드 구조 사전 경고 (GATE 4 BLOCKING 조기 발견)

    목적: Excel 생성 전에 다이아몬드 구조 문제를 조기 발견하여
          불필요한 토큰 낭비 방지 (~60,000 tokens 절약 가능)

    규칙: 고장형태당 고장원인 >= 2개 필수
    """
    from collections import defaultdict

    mode_to_causes = defaultdict(set)

    for item in items:
        # 고장형태에서 태그 제거하고 실제 형태만 추출
        mode_raw = item.get('고장형태', '')
        # 태그(부족:, 과도:, 유해:) 제거
        mode = mode_raw
        for tag in ['부족:', '과도:', '유해:']:
            mode = mode.replace(tag, '')
        mode = mode.strip()

        cause = item.get('고장원인', '').strip()

        if mode and cause:
            mode_to_causes[mode].add(cause)

    # 원인이 2개 미만인 고장형태 찾기
    single_cause_modes = [(m, len(c)) for m, c in mode_to_causes.items() if len(c) < 2]
    total_modes = len(mode_to_causes)

    if single_cause_modes:
        avg_causes = sum(len(c) for c in mode_to_causes.values()) / max(total_modes, 1)
        return {
            'valid': False,
            'avg_causes': avg_causes,
            'total_modes': total_modes,
            'single_cause_modes': single_cause_modes,
            'message': f"형태당 원인 평균 {avg_causes:.2f}개 (>=2.0 필수)"
        }

    avg_causes = sum(len(c) for c in mode_to_causes.values()) / max(total_modes, 1)
    return {
        'valid': True,
        'avg_causes': avg_causes,
        'total_modes': total_modes,
        'message': f"형태당 원인 평균 {avg_causes:.2f}개 [O]"
    }


def main():
    if len(sys.argv) < 2:
        print("사용법: python validate_fmea_json.py input_data.json")
        sys.exit(1)

    json_path = sys.argv[1]

    # JSON 파일 로드
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERROR] JSON 파일 로드 실패: {e}")
        sys.exit(1)

    items = data.get('fmea_data', [])
    total = len(items)

    print("=" * 60)
    print("[GATE 3 사전 검증] 컬럼 형식 검증 (스크립트 기반)")
    print("=" * 60)
    print(f"총 항목 수: {total}개\n")

    all_violations = {}

    # 각 컬럼 검증
    print("### E열 (고장형태) 검증...")
    e_violations = validate_column_e(items)
    if e_violations:
        all_violations['E열'] = e_violations
        print(f"   [X] {len(e_violations)}건 위반")
    else:
        print(f"   [O] 통과 ({total}개)")

    print("### C열 (고장영향) 검증...")
    c_violations = validate_column_c(items)
    if c_violations:
        all_violations['C열'] = c_violations
        print(f"   [X] {len(c_violations)}건 위반")
    else:
        print(f"   [O] 통과 ({total}개)")

    print("### F열 (고장원인) 검증...")
    f_violations = validate_column_f(items)
    if f_violations:
        all_violations['F열'] = f_violations
        print(f"   [X] {len(f_violations)}건 위반")
    else:
        print(f"   [O] 통과 ({total}개)")

    print("### G열 (고장메커니즘) 검증...")
    g_violations = validate_column_g(items)
    if g_violations:
        all_violations['G열'] = g_violations
        print(f"   [X] {len(g_violations)}건 위반")
    else:
        print(f"   [O] 통과 ({total}개)")

    print("### H열 (현재예방대책) 검증...")
    h_violations = validate_column_h(items)
    if h_violations:
        all_violations['H열'] = h_violations
        print(f"   [X] {len(h_violations)}건 위반")
    else:
        print(f"   [O] 통과 ({total}개)")

    print("### J열 (현재검출대책) 검증...")
    j_violations = validate_column_j(items)
    if j_violations:
        all_violations['J열'] = j_violations
        print(f"   [X] {len(j_violations)}건 위반")
    else:
        print(f"   [O] 통과 ({total}개)")

    # 인과관계 체인 검증 (CRITICAL - batch2 층간단락-턴수오류 문제 방지)
    print("\n### E->F 인과관계 체인 검증...")
    causal_violations = validate_causal_relationships(items)
    if causal_violations:
        all_violations['인과관계'] = causal_violations
        print(f"   [X] {len(causal_violations)}건 인과관계 불일치")
        for v in causal_violations[:3]:
            print(f"      {v}")
        if len(causal_violations) > 3:
            print(f"      ... 외 {len(causal_violations) - 3}건")
    else:
        print(f"   [O] 통과 ({total}개)")

    # 라이프사이클 밸런스 검증
    print("\n### F열 라이프사이클 밸런스 검증...")
    lifecycle_result = validate_lifecycle_balance(items)
    if not lifecycle_result['valid']:
        all_violations['라이프사이클'] = lifecycle_result['violations']
        print(f"   [X] 라이프사이클 불균형")
        for v in lifecycle_result['violations']:
            print(f"      {v}")
    else:
        sc = lifecycle_result['stage_count']
        t = lifecycle_result['total']
        print(f"   [O] 통과 - 설계:{sc['설계']}({sc['설계']/t*100:.0f}%), 재료:{sc['재료']}({sc['재료']/t*100:.0f}%), 제작:{sc['제작']}({sc['제작']/t*100:.0f}%), 시험:{sc['시험']}({sc['시험']/t*100:.0f}%)")
        if lifecycle_result.get('warnings'):
            for w in lifecycle_result['warnings']:
                print(f"      {w}")

    # 다이아몬드 구조 사전 검증 (GATE 4 BLOCKING 조기 발견)
    print("\n### 다이아몬드 구조 사전 검증...")
    diamond_result = validate_diamond_preview(items)
    diamond_warning = False
    if not diamond_result['valid']:
        diamond_warning = True
        print(f"   [WARN] {diamond_result['message']}")
        print(f"   -> 고장형태 {diamond_result['total_modes']}개 중 원인 1개만 있는 형태:")
        for mode, count in diamond_result['single_cause_modes'][:5]:
            print(f"      - \"{mode[:40]}...\" (원인 {count}개)")
        if len(diamond_result['single_cause_modes']) > 5:
            print(f"      ... 외 {len(diamond_result['single_cause_modes']) - 5}개")
        print("\n   [!] GATE 4에서 BLOCKING 예상! 지금 수정하세요:")
        print("       -> 각 고장형태에 서로 다른 원인 2개 이상 필요")
        print("       -> 예: 30개 항목 = 15개 형태 x 2개 원인")
    else:
        print(f"   [O] 통과 - {diamond_result['message']}")

    print("\n" + "=" * 60)

    # 결과 출력
    if all_violations:
        print("[GATE 3 FAIL] 컬럼 형식 검증 실패!")
        print("=" * 60)
        total_violations = sum(len(v) for v in all_violations.values())
        print(f"\n총 {total_violations}건 위반:\n")

        for column, violations in all_violations.items():
            print(f"\n### {column} 위반 목록:")
            for v in violations[:10]:  # 최대 10건만 출력
                print(v)
            if len(violations) > 10:
                print(f"  ... 외 {len(violations) - 10}건")

        print("\n" + "-" * 60)
        print("[!] JSON 파일을 수정한 후 다시 검증하세요.")
        print("-" * 60)
        sys.exit(1)
    else:
        print("[GATE 3 PASS] 모든 컬럼 형식 검증 통과!")
        print("=" * 60)
        print(f"\n검증 완료: {total}개 항목")
        print("\n-> Excel 생성 진행 가능")
        sys.exit(0)


if __name__ == "__main__":
    main()
