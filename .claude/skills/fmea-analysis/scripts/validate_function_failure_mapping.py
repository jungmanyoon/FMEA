# -*- coding: utf-8 -*-
"""
기능-고장형태 논리 연결 검증 스크립트
FMEA Excel 생성 시 GATE 4에서 사용

기준: 회의 합의 260109 (임채익 이사 피드백)
참조: references/5why-vs-fmea.md

검증 항목:
1. 원인/메커니즘 혼동 검사 (피로 파손, 임의 사용 등)
2. 고장형태(E열)에 미래 영향 포함 여부 검사
3. 시점 기반 컬럼 배치 검증

사용법:
    python validate_function_failure_mapping.py <excel_file>
    python validate_function_failure_mapping.py 철심_FMEA.xlsx

반환:
    - 검증 통과: exit code 0, JSON {"status": "pass", "violations": []}
    - 검증 실패: exit code 1, JSON {"status": "fail", "violations": [...]}
"""

import sys
import io
import json
import pandas as pd
from pathlib import Path

# Windows cp949 인코딩 문제 해결
if sys.stdout:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ============================================================================
# 원인/형태 혼동 패턴 (E열에서 금지)
# ============================================================================

# 형태+메커니즘 복합 표현 (메커니즘은 G열로 분리)
MECHANISM_IN_MODE_PATTERNS = [
    # 패턴: (검출 문자열, 올바른 분리 제안)
    ('피로 파손', 'E열: "파손", G열: "피로 -> 파손"'),
    ('피로파손', 'E열: "파손", G열: "피로 -> 파손"'),
    ('부식 파손', 'E열: "파손", G열: "부식 -> 파손"'),
    ('부식파손', 'E열: "파손", G열: "부식 -> 파손"'),
    ('열화 파손', 'E열: "파손", G열: "열화 -> 파손"'),
    ('열화파손', 'E열: "파손", G열: "열화 -> 파손"'),
    ('마모 파손', 'E열: "파손", G열: "마모 -> 파손"'),
    ('마모파손', 'E열: "파손", G열: "마모 -> 파손"'),
    ('크리프 파손', 'E열: "파손", G열: "크리프 -> 파손"'),
    ('크리프파손', 'E열: "파손", G열: "크리프 -> 파손"'),
]

# 원인(F열)이 형태(E열)에 있는 경우
CAUSE_IN_MODE_PATTERNS = [
    # 패턴: (검출 문자열, 올바른 위치)
    ('임의 사용', 'F열 (고장원인): "설계: 임의 사용"'),
    ('임의사용', 'F열 (고장원인): "설계: 임의 사용"'),
    ('설계 미흡', 'F열 (고장원인): "설계: [구체적 내용]"'),
    ('설계미흡', 'F열 (고장원인): "설계: [구체적 내용]"'),
    ('제조 불량', 'F열 (고장원인): "제조: [구체적 내용]"'),
    ('제조불량', 'F열 (고장원인): "제조: [구체적 내용]"'),
    ('조립 불량', 'F열 (고장원인): "제조: [구체적 내용]"'),
    ('조립불량', 'F열 (고장원인): "제조: [구체적 내용]"'),
    ('작업자 실수', 'F열 (고장원인): "운영: [구체적 내용]"'),
    ('작업자실수', 'F열 (고장원인): "운영: [구체적 내용]"'),
    ('유지보수 미흡', 'F열 (고장원인): "운영: [구체적 내용]"'),
    ('유지보수미흡', 'F열 (고장원인): "운영: [구체적 내용]"'),
]

# 미래 영향(C열)이 형태(E열)에 있는 경우
EFFECT_IN_MODE_PATTERNS = [
    # 패턴: (검출 문자열, 올바른 위치)
    ('소음 발생', 'C열 (고장영향): "소음 기준 초과"'),
    ('소음발생', 'C열 (고장영향): "소음 기준 초과"'),
    ('진동 발생', 'C열 (고장영향): "진동 기준 초과"'),
    ('진동발생', 'C열 (고장영향): "진동 기준 초과"'),
    ('효율 저하', 'C열 (고장영향): "효율 저하"'),
    ('효율저하', 'C열 (고장영향): "효율 저하"'),
    ('온도 상승', 'C열 (고장영향): "과열" 또는 E열: "과열"'),
    ('온도상승', 'C열 (고장영향): "과열" 또는 E열: "과열"'),
    ('화재 발생', 'C열 (고장영향): "화재"'),
    ('화재발생', 'C열 (고장영향): "화재"'),
    ('폭발', 'C열 (고장영향): "폭발"'),
    ('정전', 'C열 (고장영향): "정전"'),
    ('트립', 'C열 (고장영향): "트립"'),
    ('오작동', 'C열 (고장영향): "오작동"'),
]

# 측정값 패턴 (G열로 이동)
MEASUREMENT_PATTERNS = [
    ('철손 증가', 'G열 (메커니즘): "와전류 -> 철손 증가"'),
    ('철손증가', 'G열 (메커니즘): "와전류 -> 철손 증가"'),
    ('여자전류 증가', 'G열 (메커니즘): "자기포화 -> 여자전류 증가"'),
    ('여자전류증가', 'G열 (메커니즘): "자기포화 -> 여자전류 증가"'),
    ('손실 증가', 'G열 (메커니즘) 또는 C열 (영향)'),
    ('손실증가', 'G열 (메커니즘) 또는 C열 (영향)'),
]


def validate_failure_mode_mapping(value: str) -> list:
    """
    단일 고장형태 값의 원인/형태 혼동 검증

    Returns:
        list of (violation_type, pattern, suggestion)
    """
    violations = []

    if pd.isna(value) or str(value).strip() == '':
        return violations

    value_str = str(value).strip()

    # 1. 메커니즘이 형태에 포함된 경우
    for pattern, suggestion in MECHANISM_IN_MODE_PATTERNS:
        if pattern in value_str:
            violations.append({
                'type': 'MECHANISM_IN_MODE',
                'pattern': pattern,
                'suggestion': suggestion,
                'reason': f'메커니즘이 형태에 포함됨: "{pattern}"'
            })

    # 2. 원인이 형태에 포함된 경우
    for pattern, suggestion in CAUSE_IN_MODE_PATTERNS:
        if pattern in value_str:
            violations.append({
                'type': 'CAUSE_IN_MODE',
                'pattern': pattern,
                'suggestion': suggestion,
                'reason': f'원인이 형태 위치에 있음: "{pattern}"'
            })

    # 3. 미래 영향이 형태에 포함된 경우
    for pattern, suggestion in EFFECT_IN_MODE_PATTERNS:
        if pattern in value_str:
            violations.append({
                'type': 'EFFECT_IN_MODE',
                'pattern': pattern,
                'suggestion': suggestion,
                'reason': f'미래 영향이 형태 위치에 있음: "{pattern}"'
            })

    # 4. 측정값이 형태에 포함된 경우
    for pattern, suggestion in MEASUREMENT_PATTERNS:
        if pattern in value_str:
            violations.append({
                'type': 'MEASUREMENT_IN_MODE',
                'pattern': pattern,
                'suggestion': suggestion,
                'reason': f'측정값이 형태 위치에 있음: "{pattern}"'
            })

    return violations


def validate_excel_file(file_path: str) -> dict:
    """
    Excel 파일의 기능-고장형태 논리 연결 검증

    Returns:
        {
            "status": "pass" | "fail",
            "total_rows": int,
            "checked_rows": int,
            "violations": [{"row": int, "value": str, "issues": [...]}]
        }
    """
    result = {
        "status": "pass",
        "total_rows": 0,
        "checked_rows": 0,
        "violations": [],
        "summary": {
            "MECHANISM_IN_MODE": 0,
            "CAUSE_IN_MODE": 0,
            "EFFECT_IN_MODE": 0,
            "MEASUREMENT_IN_MODE": 0
        }
    }

    try:
        df = pd.read_excel(file_path, sheet_name='FMEA', header=None)
        result["total_rows"] = len(df)

        # 헤더 행 찾기 (고장형태 열 위치 확인)
        failure_mode_col = None
        header_row = None

        for i in range(min(10, len(df))):
            row = df.iloc[i]
            for j, val in enumerate(row):
                if str(val).strip() == '고장형태':
                    failure_mode_col = j
                    header_row = i
                    break
            if failure_mode_col is not None:
                break

        if failure_mode_col is None:
            return {
                "status": "error",
                "message": "고장형태 열을 찾을 수 없습니다.",
                "violations": []
            }

        # 데이터 행 검증
        for i in range(header_row + 1, len(df)):
            value = df.iloc[i, failure_mode_col]

            if pd.isna(value) or str(value).strip() == '':
                continue

            result["checked_rows"] += 1
            issues = validate_failure_mode_mapping(value)

            if issues:
                result["violations"].append({
                    "row": i + 1,
                    "value": str(value),
                    "issues": issues
                })

                for issue in issues:
                    result["summary"][issue["type"]] += 1

        if result["violations"]:
            result["status"] = "fail"

    except FileNotFoundError:
        return {
            "status": "error",
            "message": f"파일을 찾을 수 없습니다: {file_path}",
            "violations": []
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "violations": []
        }

    return result


def print_report(result: dict):
    """검증 결과 보고서 출력"""
    print("\n" + "=" * 70)
    print("[VALIDATE] Function-FailureMode Logic Mapping Check")
    print("기준: 회의 합의 260109 (임채익 이사 피드백)")
    print("참조: references/5why-vs-fmea.md")
    print("=" * 70)

    if result["status"] == "error":
        print(f"[ERROR] {result.get('message', 'Unknown error')}")
        return

    print(f"Total rows: {result['total_rows']}")
    print(f"Checked rows: {result['checked_rows']}")
    print(f"Violations: {len(result['violations'])}")
    print("-" * 70)

    if "summary" in result:
        print("\n[Summary by Type]")
        print(f"  MECHANISM_IN_MODE (메커니즘이 형태에): {result['summary']['MECHANISM_IN_MODE']}")
        print(f"  CAUSE_IN_MODE (원인이 형태에): {result['summary']['CAUSE_IN_MODE']}")
        print(f"  EFFECT_IN_MODE (영향이 형태에): {result['summary']['EFFECT_IN_MODE']}")
        print(f"  MEASUREMENT_IN_MODE (측정값이 형태에): {result['summary']['MEASUREMENT_IN_MODE']}")
        print()

    if result["status"] == "pass":
        print("[PASS] No logic mapping issues found.")
    else:
        print("[FAIL] Please fix the following items:\n")

        for v in result["violations"]:
            print(f"  Row {v['row']}: \"{v['value']}\"")
            for issue in v["issues"]:
                print(f"    - {issue['reason']}")
                print(f"      -> 수정: {issue['suggestion']}")
            print()

        print("-" * 70)
        print("[시점 기반 컬럼 구분 가이드]")
        print("  ┌─────────┬──────────────┬─────────────────────────┐")
        print("  │  시점   │    컬럼      │        내용             │")
        print("  ├─────────┼──────────────┼─────────────────────────┤")
        print("  │  과거   │ F열 (원인)   │ 왜 발생했나?            │")
        print("  │  현재   │ E열 (형태)   │ 지금 관찰 가능한 현상   │")
        print("  │  미래   │ C열 (영향)   │ 앞으로 무슨 일?         │")
        print("  │  과정   │ G열 (메커니즘)│ 원인->과정->결과         │")
        print("  └─────────┴──────────────┴─────────────────────────┘")
        print()
        print("[참조 문서]")
        print("  - references/5why-vs-fmea.md (5 Why vs FMEA 비교)")
        print("  - references/column-details.md (컬럼별 상세 정의)")
        print("  - references/failure-mode-forbidden.md (금지어 목록)")

    print("=" * 70)


def main():
    if len(sys.argv) < 2:
        print("사용법: python validate_function_failure_mapping.py <excel_file>")
        print("예시: python validate_function_failure_mapping.py 철심_FMEA.xlsx")
        print()
        print("검증 항목:")
        print("  1. 메커니즘이 형태에 포함 (피로 파손 -> 파손 + 피로 분리)")
        print("  2. 원인이 형태에 포함 (임의 사용 -> F열로 이동)")
        print("  3. 미래 영향이 형태에 포함 (소음 발생 -> C열로 이동)")
        print("  4. 측정값이 형태에 포함 (철손 증가 -> G열로 이동)")
        sys.exit(1)

    file_path = sys.argv[1]
    result = validate_excel_file(file_path)

    print_report(result)

    print("\n[JSON Output]")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result["status"] == "pass":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
