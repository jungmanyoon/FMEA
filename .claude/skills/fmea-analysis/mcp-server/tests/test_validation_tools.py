#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FMEA MCP Server - Unit Tests

Version: 1.0
Date: 2026-02-04

[!] Tests internal logic functions directly (not MCP tool wrappers)
"""

import sys
import os
import tempfile
import hashlib

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import (
    # Internal logic functions (testable)
    _validate_failure_mode_logic,
    _validate_effect_logic,
    _validate_cause_logic,
    _validate_mechanism_logic,
    _validate_prevention_logic,
    _validate_detection_logic,
    _validate_causal_chain_logic,
    # Constants
    FORBIDDEN_MECHANISMS,
    FORBIDDEN_MEASUREMENTS,
    FORBIDDEN_FUTURE_RESULTS,
    INVALID_CAUSAL_COMBINATIONS,
)

# ============================================================
# Test: fmea_validate_failure_mode (E Column)
# ============================================================

def test_failure_mode_pass_with_tag():
    """[PASS] Tag present with valid phenomenon"""
    result = _validate_failure_mode_logic("부족: 층간단락")
    assert result["status"] == "pass", f"Expected pass, got {result}"
    assert result["violation_count"] == 0
    print("[O] test_failure_mode_pass_with_tag: PASSED")

def test_failure_mode_fail_missing_tag():
    """[FAIL] Missing required tag"""
    result = _validate_failure_mode_logic("층간단락")
    assert result["status"] == "fail"
    assert any(v["type"] == "MISSING_TAG" for v in result["violations"])
    print("[O] test_failure_mode_fail_missing_tag: PASSED")

def test_failure_mode_fail_mechanism_word():
    """[FAIL] Mechanism word in E column"""
    result = _validate_failure_mode_logic("부족: 피로")
    assert result["status"] == "fail"
    assert any(v["type"] == "MECHANISM_IN_E" for v in result["violations"])
    print("[O] test_failure_mode_fail_mechanism_word: PASSED")

def test_failure_mode_fail_measurement_word():
    """[FAIL] Measurement word in E column"""
    result = _validate_failure_mode_logic("부족: 온도상승")
    assert result["status"] == "fail"
    assert any(v["type"] == "MEASUREMENT_IN_E" for v in result["violations"])
    print("[O] test_failure_mode_fail_measurement_word: PASSED")

def test_failure_mode_fail_future_result():
    """[FAIL] Future result word in E column"""
    result = _validate_failure_mode_logic("부족: 소음")
    assert result["status"] == "fail"
    assert any(v["type"] == "FUTURE_RESULT_IN_E" for v in result["violations"])
    print("[O] test_failure_mode_fail_future_result: PASSED")

# ============================================================
# Test: fmea_validate_effect (C Column)
# ============================================================

def test_effect_pass():
    """[PASS] Future effect without physical state"""
    result = _validate_effect_logic("고객 정전 발생")
    assert result["status"] == "pass"
    print("[O] test_effect_pass: PASSED")

def test_effect_fail_physical_state():
    """[FAIL] Physical state in C column"""
    result = _validate_effect_logic("크랙 발생")
    assert result["status"] == "fail"
    assert any(v["type"] == "PHYSICAL_STATE_IN_C" for v in result["violations"])
    print("[O] test_effect_fail_physical_state: PASSED")

# ============================================================
# Test: fmea_validate_cause (F Column)
# ============================================================

def test_cause_pass_with_lifecycle():
    """[PASS] Lifecycle tag present"""
    result = _validate_cause_logic("설계: 절연거리 불충분")
    assert result["status"] == "pass"
    print("[O] test_cause_pass_with_lifecycle: PASSED")

def test_cause_fail_missing_lifecycle():
    """[FAIL] Missing lifecycle tag"""
    result = _validate_cause_logic("절연거리 불충분")
    assert result["status"] == "fail"
    assert any(v["type"] == "MISSING_LIFECYCLE" for v in result["violations"])
    print("[O] test_cause_fail_missing_lifecycle: PASSED")

# ============================================================
# Test: fmea_validate_mechanism (G Column)
# ============================================================

def test_mechanism_pass():
    """[PASS] 2+ arrows present"""
    result = _validate_mechanism_logic("열화 -> 절연저하 -> 단락")
    assert result["status"] == "pass"
    assert result["arrow_count"] >= 2
    print("[O] test_mechanism_pass: PASSED")

def test_mechanism_fail_insufficient_arrows():
    """[FAIL] Less than 2 arrows"""
    result = _validate_mechanism_logic("열화 -> 단락")
    assert result["status"] == "fail"
    assert result["arrow_count"] < 2
    print("[O] test_mechanism_fail_insufficient_arrows: PASSED")

# ============================================================
# Test: fmea_validate_prevention (H Column)
# ============================================================

def test_prevention_pass():
    """[PASS] 4+ lines present"""
    prevention = """설계: IEC 60076 적용
재료: KS C IEC 규격 자재
제작: 절연저항 측정
시험: 유도시험 실시"""
    result = _validate_prevention_logic(prevention)
    assert result["status"] == "pass"
    assert result["line_count"] >= 4
    print("[O] test_prevention_pass: PASSED")

def test_prevention_fail_insufficient_lines():
    """[FAIL] Less than 4 lines"""
    prevention = """설계: IEC 60076 적용
재료: KS C IEC 규격 자재"""
    result = _validate_prevention_logic(prevention)
    assert result["status"] == "fail"
    assert result["line_count"] < 4
    print("[O] test_prevention_fail_insufficient_lines: PASSED")

# ============================================================
# Test: fmea_validate_detection (J Column)
# ============================================================

def test_detection_pass():
    """[PASS] 4+ lines present"""
    detection = """설계: 도면검토
재료: 입고검사
제작: 공정검사
시험: 최종시험"""
    result = _validate_detection_logic(detection)
    assert result["status"] == "pass"
    assert result["line_count"] >= 4
    print("[O] test_detection_pass: PASSED")

def test_detection_fail_insufficient_lines():
    """[FAIL] Less than 4 lines"""
    detection = """설계: 도면검토"""
    result = _validate_detection_logic(detection)
    assert result["status"] == "fail"
    print("[O] test_detection_fail_insufficient_lines: PASSED")

# ============================================================
# Test: fmea_validate_causal_chain (E->F)
# ============================================================

def test_causal_chain_pass():
    """[PASS] Valid causal relationship"""
    result = _validate_causal_chain_logic(
        "부족: 층간단락",
        "설계: 절연거리 불충분"
    )
    assert result["status"] == "pass"
    print("[O] test_causal_chain_pass: PASSED")

def test_causal_chain_fail_invalid_combination():
    """[FAIL] Invalid causal combination"""
    result = _validate_causal_chain_logic(
        "부족: 층간단락",
        "설계: 턴수설계오류"
    )
    assert result["status"] == "fail"
    assert any(v["type"] == "INVALID_CAUSAL_CHAIN" for v in result["violations"])
    print("[O] test_causal_chain_fail_invalid_combination: PASSED")

# ============================================================
# Test: Constants
# ============================================================

def test_forbidden_mechanisms():
    """[PASS] Forbidden mechanisms list exists"""
    assert len(FORBIDDEN_MECHANISMS) > 0
    assert "피로" in FORBIDDEN_MECHANISMS
    print("[O] test_forbidden_mechanisms: PASSED")

def test_forbidden_measurements():
    """[PASS] Forbidden measurements list exists"""
    assert len(FORBIDDEN_MEASUREMENTS) > 0
    assert "증가" in FORBIDDEN_MEASUREMENTS
    print("[O] test_forbidden_measurements: PASSED")

def test_forbidden_future_results():
    """[PASS] Forbidden future results list exists"""
    assert len(FORBIDDEN_FUTURE_RESULTS) > 0
    assert "소음" in FORBIDDEN_FUTURE_RESULTS
    print("[O] test_forbidden_future_results: PASSED")

def test_invalid_causal_combinations():
    """[PASS] Invalid causal combinations dict exists"""
    assert "층간단락" in INVALID_CAUSAL_COMBINATIONS
    assert len(INVALID_CAUSAL_COMBINATIONS["층간단락"]) > 0
    print("[O] test_invalid_causal_combinations: PASSED")

# ============================================================
# Test: fmea_create_item (환각 방지)
# ============================================================

# Note: fmea_create_item은 MCP 도구이므로 _read_files 전역 상태에 의존
# 여기서는 내부 검증 로직만 테스트 (출처 확인은 통합 테스트에서)

def test_create_item_validation_all_pass():
    """[PASS] All columns pass validation"""
    # E열
    fm = _validate_failure_mode_logic("부족: 층간단락")
    assert fm["status"] == "pass"
    # F열
    cause = _validate_cause_logic("설계: 절연거리 불충분")
    assert cause["status"] == "pass"
    # G열
    mech = _validate_mechanism_logic("절연열화 -> 부분방전 -> 단락")
    assert mech["status"] == "pass"
    # C열
    eff = _validate_effect_logic("고객 정전 발생")
    assert eff["status"] == "pass"
    # H열
    prev = _validate_prevention_logic("설계: IEC 적용\n재료: KS 규격\n제작: 검사\n시험: 유도시험")
    assert prev["status"] == "pass"
    # J열
    det = _validate_detection_logic("설계: 도면검토\n재료: 입고검사\n제작: 공정검사\n시험: 최종시험")
    assert det["status"] == "pass"
    print("[O] test_create_item_validation_all_pass: PASSED")

def test_create_item_validation_e_fail():
    """[FAIL] E column fails -> create_item should fail"""
    fm = _validate_failure_mode_logic("피로")  # 메커니즘 금지어 + 태그 없음
    assert fm["status"] == "fail"
    assert fm["violation_count"] >= 1
    print("[O] test_create_item_validation_e_fail: PASSED")

# ============================================================
# Main
# ============================================================

def run_all_tests():
    """Run all unit tests"""
    print("=" * 60)
    print("FMEA MCP Server - Unit Tests")
    print("=" * 60)

    tests = [
        # E Column
        test_failure_mode_pass_with_tag,
        test_failure_mode_fail_missing_tag,
        test_failure_mode_fail_mechanism_word,
        test_failure_mode_fail_measurement_word,
        test_failure_mode_fail_future_result,
        # C Column
        test_effect_pass,
        test_effect_fail_physical_state,
        # F Column
        test_cause_pass_with_lifecycle,
        test_cause_fail_missing_lifecycle,
        # G Column
        test_mechanism_pass,
        test_mechanism_fail_insufficient_arrows,
        # H Column
        test_prevention_pass,
        test_prevention_fail_insufficient_lines,
        # J Column
        test_detection_pass,
        test_detection_fail_insufficient_lines,
        # E->F Causal Chain
        test_causal_chain_pass,
        test_causal_chain_fail_invalid_combination,
        # Constants
        test_forbidden_mechanisms,
        test_forbidden_measurements,
        test_forbidden_future_results,
        test_invalid_causal_combinations,
        # Create Item (integration validation)
        test_create_item_validation_all_pass,
        test_create_item_validation_e_fail,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"[X] {test.__name__}: FAILED - {e}")
            failed += 1
        except Exception as e:
            print(f"[X] {test.__name__}: ERROR - {e}")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
