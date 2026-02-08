# -*- coding: utf-8 -*-
"""
인과관계 체인 검증 스크립트
형태->원인, 원인->메커니즘 인과관계 검증

사용법:
    python validate_causal_chain.py <excel_file>
    python validate_causal_chain.py 철심_FMEA.xlsx

반환:
    - 검증 통과: exit code 0, JSON {"status": "pass", ...}
    - 검증 실패: exit code 1, JSON {"status": "fail", ...}

온톨로지:
    - references/causal-chain-ontology.md에서 규칙 동적 로드
"""

import sys
import io
import json
import re
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple

# Windows cp949 인코딩 문제 해결 (공통 모듈 사용)
from encoding_utils import setup_encoding
setup_encoding()

# 스크립트 디렉토리
script_dir = Path(__file__).parent


def load_causal_chain_ontology() -> dict:
    """
    causal-chain-ontology.md에서 인과관계 규칙 동적 로드

    Returns:
        {
            'mode_cause_valid': {카테고리: {고장형태: [...], 유효원인: [...]}},
            'cause_mechanism_valid': {카테고리: {원인: [...], 유효메커니즘: [...]}},
            'invalid_mode_cause': {고장형태: [무효원인들]},
            'invalid_cause_mechanism': {원인: [무효메커니즘들]},
            'lifecycle_cause_map': {단계: {원인키워드: [...], 메커니즘키워드: [...]}}
        }
    """
    ontology_path = script_dir.parent / "references" / "causal-chain-ontology.md"

    result = {
        'mode_cause_valid': {},
        'cause_mechanism_valid': {},
        'invalid_mode_cause': {},
        'invalid_cause_mechanism': {},
        'lifecycle_cause_map': {}
    }

    if not ontology_path.exists():
        print(f"[WARNING] 온톨로지 파일 없음: {ontology_path}")
        return result

    content = ontology_path.read_text(encoding='utf-8')

    # SECTION 기반 파싱
    sections = re.split(r'\n## SECTION:', content)

    for section in sections:
        lines = section.strip().split('\n')
        if not lines:
            continue

        section_name = lines[0].strip()

        # MODE_CAUSE_VALID
        if section_name == 'MODE_CAUSE_VALID':
            current_category = None
            for line in lines[1:]:
                if line.strip().startswith('---'):
                    break
                cat_match = re.match(r'### CATEGORY:(.+)', line)
                if cat_match:
                    current_category = cat_match.group(1).strip()
                    result['mode_cause_valid'][current_category] = {'고장형태': [], '유효원인': []}
                elif current_category and ':' in line:
                    if line.startswith('고장형태:'):
                        _, keywords = line.split(':', 1)
                        result['mode_cause_valid'][current_category]['고장형태'] = [
                            k.strip() for k in keywords.split(',') if k.strip()
                        ]
                    elif line.startswith('유효원인:'):
                        _, keywords = line.split(':', 1)
                        result['mode_cause_valid'][current_category]['유효원인'] = [
                            k.strip() for k in keywords.split(',') if k.strip()
                        ]

        # CAUSE_MECHANISM_VALID
        elif section_name == 'CAUSE_MECHANISM_VALID':
            current_category = None
            for line in lines[1:]:
                if line.strip().startswith('---'):
                    break
                cat_match = re.match(r'### CATEGORY:(.+)', line)
                if cat_match:
                    current_category = cat_match.group(1).strip()
                    result['cause_mechanism_valid'][current_category] = {'원인': [], '유효메커니즘': []}
                elif current_category and ':' in line:
                    if line.startswith('원인:'):
                        _, keywords = line.split(':', 1)
                        result['cause_mechanism_valid'][current_category]['원인'] = [
                            k.strip() for k in keywords.split(',') if k.strip()
                        ]
                    elif line.startswith('유효메커니즘:'):
                        _, keywords = line.split(':', 1)
                        result['cause_mechanism_valid'][current_category]['유효메커니즘'] = [
                            k.strip() for k in keywords.split(',') if k.strip()
                        ]

        # INVALID_COMBINATIONS
        elif section_name == 'INVALID_COMBINATIONS':
            current_type = None
            for line in lines[1:]:
                if line.strip().startswith('---'):
                    break
                if '### MODE_CAUSE:' in line:
                    current_type = 'mode_cause'
                elif '### CAUSE_MECHANISM:' in line:
                    current_type = 'cause_mechanism'
                elif current_type and ':' in line and not line.startswith('#'):
                    key, values = line.split(':', 1)
                    key = key.strip()
                    invalid_list = [v.strip() for v in values.split(',') if v.strip()]
                    if current_type == 'mode_cause':
                        result['invalid_mode_cause'][key] = invalid_list
                    else:
                        result['invalid_cause_mechanism'][key] = invalid_list

        # LIFECYCLE_CAUSE_MAP
        elif section_name == 'LIFECYCLE_CAUSE_MAP':
            current_stage = None
            for line in lines[1:]:
                if line.strip().startswith('---'):
                    break
                stage_match = re.match(r'### STAGE:(.+)', line)
                if stage_match:
                    current_stage = stage_match.group(1).strip()
                    result['lifecycle_cause_map'][current_stage] = {'원인키워드': [], '메커니즘키워드': []}
                elif current_stage and ':' in line:
                    if line.startswith('원인키워드:'):
                        _, keywords = line.split(':', 1)
                        result['lifecycle_cause_map'][current_stage]['원인키워드'] = [
                            k.strip() for k in keywords.split(',') if k.strip()
                        ]
                    elif line.startswith('메커니즘키워드:'):
                        _, keywords = line.split(':', 1)
                        result['lifecycle_cause_map'][current_stage]['메커니즘키워드'] = [
                            k.strip() for k in keywords.split(',') if k.strip()
                        ]

    return result


# 온톨로지 로드 (모듈 로드 시 1회)
_ontology = load_causal_chain_ontology()

# 상수 내보내기
MODE_CAUSE_VALID = _ontology['mode_cause_valid']
CAUSE_MECHANISM_VALID = _ontology['cause_mechanism_valid']
INVALID_MODE_CAUSE = _ontology['invalid_mode_cause']
INVALID_CAUSE_MECHANISM = _ontology['invalid_cause_mechanism']
LIFECYCLE_CAUSE_MAP = _ontology['lifecycle_cause_map']


def find_category_for_mode(mode: str) -> Optional[str]:
    """고장형태가 속한 카테고리 찾기"""
    for category, data in MODE_CAUSE_VALID.items():
        for known_mode in data['고장형태']:
            if known_mode in mode:
                return category
    return None


def find_category_for_cause(cause: str) -> Optional[str]:
    """원인이 속한 카테고리 찾기"""
    for category, data in CAUSE_MECHANISM_VALID.items():
        for known_cause in data['원인']:
            if known_cause in cause:
                return category
    return None


def validate_mode_cause(mode: str, cause: str) -> Tuple[bool, str]:
    """
    형태 -> 원인 인과관계 검증

    Args:
        mode: 고장형태 (E열)
        cause: 고장원인 (F열)

    Returns:
        (is_valid, reason)
    """
    if pd.isna(mode) or pd.isna(cause):
        return True, "빈 값"

    mode_str = str(mode).strip()
    cause_str = str(cause).strip()

    # 태그 제거 (부족:, 과도:, 유해:)
    for tag in ['부족:', '과도:', '유해:']:
        if tag in mode_str:
            mode_str = mode_str.split(tag, 1)[1].strip()
            break

    # 명시적 무효 조합 체크
    for invalid_mode, invalid_causes in INVALID_MODE_CAUSE.items():
        if invalid_mode in mode_str:
            for invalid_cause in invalid_causes:
                if invalid_cause in cause_str:
                    return False, f"무효 조합: '{mode_str}' <- '{invalid_cause}' (인과관계 불성립)"

    # 카테고리 기반 유효성 검증 [BLOCKING으로 강화]
    category = find_category_for_mode(mode_str)
    if category:
        valid_causes = MODE_CAUSE_VALID[category]['유효원인']
        has_valid = any(vc in cause_str for vc in valid_causes)
        if not has_valid:
            return False, f"[BLOCKING] '{category}' 고장형태에 유효 원인 없음 - 인과관계 재검토 필요"

    return True, "OK"


def validate_cause_mechanism(cause: str, mechanism: str) -> Tuple[bool, str]:
    """
    원인 -> 메커니즘 인과관계 검증

    Args:
        cause: 고장원인 (F열)
        mechanism: 고장메커니즘 (G열)

    Returns:
        (is_valid, reason)
    """
    if pd.isna(cause) or pd.isna(mechanism):
        return True, "빈 값"

    cause_str = str(cause).strip()
    mechanism_str = str(mechanism).strip()

    # 명시적 무효 조합 체크
    for invalid_cause, invalid_mechanisms in INVALID_CAUSE_MECHANISM.items():
        if invalid_cause in cause_str:
            for invalid_mech in invalid_mechanisms:
                if invalid_mech in mechanism_str:
                    return False, f"무효 조합: '{invalid_cause}' -> '{invalid_mech}' (메커니즘 불일치)"

    # 카테고리 기반 유효성 검증
    category = find_category_for_cause(cause_str)
    if category:
        valid_mechanisms = CAUSE_MECHANISM_VALID[category]['유효메커니즘']
        has_valid = any(vm in mechanism_str for vm in valid_mechanisms)
        if not has_valid:
            return True, f"[WARN] '{category}' 원인에 예상 메커니즘 없음 - 검토 권장"

    return True, "OK"


def validate_lifecycle_consistency(cause: str, mechanism: str) -> Tuple[bool, str, Optional[str]]:
    """
    라이프사이클 단계 일관성 검증

    Returns:
        (is_valid, reason, detected_stage)
    """
    if pd.isna(cause) or pd.isna(mechanism):
        return True, "빈 값", None

    cause_str = str(cause).strip()
    mechanism_str = str(mechanism).strip()

    cause_stage = None
    mechanism_stage = None

    # 원인에서 라이프사이클 단계 추출
    for stage, data in LIFECYCLE_CAUSE_MAP.items():
        for keyword in data['원인키워드']:
            if keyword in cause_str:
                cause_stage = stage
                break
        if cause_stage:
            break

    # 메커니즘에서 라이프사이클 단계 추출
    for stage, data in LIFECYCLE_CAUSE_MAP.items():
        for keyword in data['메커니즘키워드']:
            if keyword in mechanism_str:
                mechanism_stage = stage
                break
        if mechanism_stage:
            break

    # 단계 일관성 검증
    if cause_stage and mechanism_stage and cause_stage != mechanism_stage:
        return False, f"라이프사이클 불일치: 원인={cause_stage}, 메커니즘={mechanism_stage}", cause_stage

    return True, "OK", cause_stage or mechanism_stage


def validate_excel_file(file_path: str) -> dict:
    """
    Excel 파일의 인과관계 체인 전체 검증

    Returns:
        {
            "status": "pass" | "fail" | "warning",
            "total_rows": int,
            "mode_cause_violations": [...],
            "cause_mechanism_violations": [...],
            "lifecycle_violations": [...],
            "warnings": [...]
        }
    """
    result = {
        "status": "pass",
        "total_rows": 0,
        "checked_rows": 0,
        "mode_cause_violations": [],
        "cause_mechanism_violations": [],
        "lifecycle_violations": [],
        "warnings": []
    }

    try:
        # FMEA 시트 읽기
        df = pd.read_excel(file_path, sheet_name='FMEA', header=None)
        result["total_rows"] = len(df)

        # 헤더 행 찾기
        header_row = None
        col_map = {}

        for i in range(min(10, len(df))):
            row = df.iloc[i]
            for j, val in enumerate(row):
                val_str = str(val).strip()
                if val_str == '고장형태':
                    col_map['고장형태'] = j
                    header_row = i
                elif val_str == '잠재적 고장원인':
                    col_map['고장원인'] = j
                elif val_str == '고장 메커니즘':
                    col_map['고장메커니즘'] = j

        if header_row is None or '고장형태' not in col_map:
            return {
                "status": "error",
                "message": "필수 열을 찾을 수 없습니다 (고장형태, 고장원인, 고장메커니즘)",
                "mode_cause_violations": [],
                "cause_mechanism_violations": []
            }

        # 데이터 행 검증
        for i in range(header_row + 1, len(df)):
            mode = df.iloc[i, col_map.get('고장형태', -1)] if '고장형태' in col_map else None
            cause = df.iloc[i, col_map.get('고장원인', -1)] if '고장원인' in col_map else None
            mechanism = df.iloc[i, col_map.get('고장메커니즘', -1)] if '고장메커니즘' in col_map else None

            if pd.isna(mode) and pd.isna(cause) and pd.isna(mechanism):
                continue

            result["checked_rows"] += 1

            # 형태 -> 원인 검증
            if mode and cause:
                mc_valid, mc_reason = validate_mode_cause(mode, cause)
                if not mc_valid:
                    result["mode_cause_violations"].append({
                        "row": i + 1,
                        "mode": str(mode),
                        "cause": str(cause),
                        "reason": mc_reason
                    })
                elif mc_reason.startswith("[WARN]"):
                    result["warnings"].append({
                        "row": i + 1,
                        "type": "mode_cause",
                        "reason": mc_reason
                    })

            # 원인 -> 메커니즘 검증
            if cause and mechanism:
                cm_valid, cm_reason = validate_cause_mechanism(cause, mechanism)
                if not cm_valid:
                    result["cause_mechanism_violations"].append({
                        "row": i + 1,
                        "cause": str(cause),
                        "mechanism": str(mechanism),
                        "reason": cm_reason
                    })
                elif cm_reason.startswith("[WARN]"):
                    result["warnings"].append({
                        "row": i + 1,
                        "type": "cause_mechanism",
                        "reason": cm_reason
                    })

            # 라이프사이클 일관성 검증
            if cause and mechanism:
                lc_valid, lc_reason, _ = validate_lifecycle_consistency(cause, mechanism)
                if not lc_valid:
                    result["lifecycle_violations"].append({
                        "row": i + 1,
                        "cause": str(cause),
                        "mechanism": str(mechanism),
                        "reason": lc_reason
                    })

        # 최종 상태 결정
        if result["mode_cause_violations"] or result["cause_mechanism_violations"] or result["lifecycle_violations"]:
            result["status"] = "fail"
        elif result["warnings"]:
            result["status"] = "warning"

    except FileNotFoundError:
        return {
            "status": "error",
            "message": f"파일을 찾을 수 없습니다: {file_path}",
            "mode_cause_violations": [],
            "cause_mechanism_violations": []
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "mode_cause_violations": [],
            "cause_mechanism_violations": []
        }

    return result


def print_report(result: dict):
    """검증 결과 보고서 출력"""
    print("\n" + "=" * 60)
    print("[VALIDATE] Causal Chain Validation (E->F->G)")
    print("=" * 60)

    if result["status"] == "error":
        print(f"[ERROR] {result.get('message', 'Unknown error')}")
        return

    print(f"Total rows: {result['total_rows']}")
    print(f"Checked rows: {result['checked_rows']}")
    print("-" * 60)

    # 형태->원인 검증 결과
    print("\n[1] Mode -> Cause Validation (E->F)")
    print(f"    Violations: {len(result['mode_cause_violations'])}")
    if result["mode_cause_violations"]:
        for v in result["mode_cause_violations"]:
            print(f"    Row {v['row']}: \"{v['mode']}\" <- \"{v['cause']}\"")
            print(f"           -> {v['reason']}")

    # 원인->메커니즘 검증 결과
    print("\n[2] Cause -> Mechanism Validation (F->G)")
    print(f"    Violations: {len(result['cause_mechanism_violations'])}")
    if result["cause_mechanism_violations"]:
        for v in result["cause_mechanism_violations"]:
            print(f"    Row {v['row']}: \"{v['cause']}\" -> \"{v['mechanism']}\"")
            print(f"           -> {v['reason']}")

    # 라이프사이클 검증 결과
    print("\n[3] Lifecycle Consistency (F-G)")
    print(f"    Violations: {len(result.get('lifecycle_violations', []))}")
    if result.get("lifecycle_violations"):
        for v in result["lifecycle_violations"]:
            print(f"    Row {v['row']}: \"{v['cause']}\" -> \"{v['mechanism']}\"")
            print(f"           -> {v['reason']}")

    # 경고
    print("\n[4] Warnings (Review Recommended)")
    print(f"    Count: {len(result.get('warnings', []))}")
    if result.get("warnings"):
        for w in result["warnings"][:5]:  # 최대 5개만 출력
            print(f"    Row {w['row']}: {w['reason']}")
        if len(result["warnings"]) > 5:
            print(f"    ... and {len(result['warnings']) - 5} more")

    print("-" * 60)

    if result["status"] == "pass":
        print("[PASS] All causal chain validations passed.")
    elif result["status"] == "warning":
        print("[WARNING] Passed with warnings. Review recommended.")
    else:
        print("[FAIL] Please fix the causal chain issues above.")
        print("\n[FIX GUIDE]")
        print("  - Mode -> Cause: Ensure cause logically leads to failure mode")
        print("  - Cause -> Mechanism: Ensure mechanism explains how cause creates mode")
        print("  - Lifecycle: Cause and mechanism should be from same lifecycle stage")
        print("  - Reference: references/causal-chain-ontology.md")

    print("=" * 60)


def main():
    if len(sys.argv) < 2:
        print("사용법: python validate_causal_chain.py <excel_file>")
        print("예시: python validate_causal_chain.py 철심_FMEA.xlsx")
        sys.exit(1)

    file_path = sys.argv[1]
    result = validate_excel_file(file_path)

    # 보고서 출력
    print_report(result)

    # JSON 결과 출력 (파이프라인 연동용)
    print("\n[JSON Output]")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 종료 코드
    if result["status"] == "pass" or result["status"] == "warning":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
