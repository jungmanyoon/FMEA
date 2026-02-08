# -*- coding: utf-8 -*-
"""
S값 범위 분포 검증 스크립트
FMEA Excel 검증: S값 범위별 고장영향 분포 확인

기준: 회의 합의 260109 (임채익 이사 피드백)
- 고장영향 = 기능 실패의 결과 (인과관계 필수)
- 발견 시점은 S값으로 반영
- "조립 불합격", "FAT 불합격" 같은 발견 장소는 고장영향이 아님
- 올바른 예시: 조립 정밀도 저하 (S=4), 무부하 손실 초과 (S=6)

Usage:
    python validate_lifecycle_coverage.py <excel_file>
    python validate_lifecycle_coverage.py CORE_FMEA.xlsx

Returns:
    - Pass: exit code 0, JSON {"status": "pass", "s_distribution": {...}}
    - Warning: exit code 0, JSON {"status": "warning", "recommendations": [...]}
"""

import sys
import io
import json
import pandas as pd
from pathlib import Path

# Windows cp949 인코딩 문제 해결
if sys.stdout:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# S값 범위 정의
S_RANGES = {
    'low': {
        'range': (2, 5),
        'display_name': 'S=2-5 (경미)',
        'korean_name': '경미한 영향',
        'description': '조기 발견 시 재작업 수준'
    },
    'medium': {
        'range': (6, 7),
        'display_name': 'S=6-7 (중간)',
        'korean_name': '중간 영향',
        'description': '시험/검사로 발견, 일정 지연'
    },
    'high': {
        'range': (8, 10),
        'display_name': 'S=8-10 (심각)',
        'korean_name': '심각한 영향',
        'description': '현장 고장, 안전 사고'
    }
}

# 발견 장소 패턴 (고장영향에서 제거 권장)
DISCOVERY_LOCATION_PATTERNS = [
    '조립 불합격', '조립불합격',
    'FAT 불합격', 'FAT불합격',
    '용접 불량', '용접불량',
    '치수 초과', '치수초과',
    '외관 불량', '외관불량',
    '시험 불합격', '시험불합격',
    '내전압 불합격', '내전압불합격',
    '절연저항 불량', '절연저항불량'
]


def classify_s_range(s_value) -> str:
    """
    S값을 범위별로 분류.

    Args:
        s_value: S값 (숫자)

    Returns:
        범위 이름: 'low', 'medium', 'high', or 'invalid'
    """
    if pd.isna(s_value):
        return 'invalid'

    try:
        s = int(s_value)
        if s < 1 or s > 10:
            return 'invalid'
        elif s <= 5:
            return 'low'
        elif s <= 7:
            return 'medium'
        else:
            return 'high'
    except (ValueError, TypeError):
        return 'invalid'


def check_discovery_location(effect_value: str) -> list:
    """
    고장영향에서 발견 장소 패턴 검출.

    Args:
        effect_value: 고장영향 텍스트 (C열)

    Returns:
        발견된 발견 장소 패턴 목록
    """
    if pd.isna(effect_value) or str(effect_value).strip() == '':
        return []

    effect_str = str(effect_value).strip()
    found_patterns = []

    for pattern in DISCOVERY_LOCATION_PATTERNS:
        if pattern in effect_str:
            found_patterns.append(pattern)

    return found_patterns


def validate_s_distribution(file_path: str) -> dict:
    """
    FMEA Excel 파일의 S값 범위 분포 검증.

    Returns:
        {
            "status": "pass" | "warning" | "error",
            "total_rows": int,
            "s_distribution": {
                "low": {"count": int, "percentage": float, "items": [...]},
                "medium": {"count": int, "percentage": float, "items": [...]},
                "high": {"count": int, "percentage": float, "items": [...]}
            },
            "discovery_location_issues": [...],
            "recommendations": [...]
        }
    """
    result = {
        "status": "pass",
        "total_rows": 0,
        "checked_rows": 0,
        "s_distribution": {
            "low": {"count": 0, "percentage": 0.0, "items": []},
            "medium": {"count": 0, "percentage": 0.0, "items": []},
            "high": {"count": 0, "percentage": 0.0, "items": []}
        },
        "discovery_location_issues": [],
        "recommendations": []
    }

    try:
        df = pd.read_excel(file_path, sheet_name='FMEA', header=None)
        result["total_rows"] = len(df)

        # 헤더 행 찾기
        effect_col = None  # C열 (고장영향)
        s_col = None       # D열 (S값)
        header_row = None

        for i in range(min(10, len(df))):
            row = df.iloc[i]
            for j, val in enumerate(row):
                val_str = str(val).strip()
                if val_str == '고장영향':
                    effect_col = j
                    header_row = i
                elif val_str == 'S':
                    s_col = j
            if effect_col is not None:
                break

        if effect_col is None:
            return {
                "status": "error",
                "message": "고장영향 열을 찾을 수 없습니다.",
                "s_distribution": {},
                "discovery_location_issues": []
            }

        if s_col is None:
            return {
                "status": "error",
                "message": "S값 열을 찾을 수 없습니다.",
                "s_distribution": {},
                "discovery_location_issues": []
            }

        # 각 데이터 행 분석
        for i in range(header_row + 1, len(df)):
            effect_value = df.iloc[i, effect_col]
            s_value = df.iloc[i, s_col]

            if pd.isna(effect_value) or str(effect_value).strip() == '':
                continue

            result["checked_rows"] += 1

            # S값 범위 분류
            s_range = classify_s_range(s_value)
            if s_range in result["s_distribution"]:
                result["s_distribution"][s_range]["count"] += 1
                if len(result["s_distribution"][s_range]["items"]) < 3:
                    result["s_distribution"][s_range]["items"].append({
                        "row": i + 1,
                        "effect": str(effect_value)[:40],
                        "s_value": int(s_value) if not pd.isna(s_value) else None
                    })

            # 발견 장소 패턴 검출
            discovery_patterns = check_discovery_location(effect_value)
            if discovery_patterns:
                result["discovery_location_issues"].append({
                    "row": i + 1,
                    "effect": str(effect_value)[:40],
                    "patterns": discovery_patterns
                })

        # 비율 계산
        total_checked = result["checked_rows"]
        if total_checked > 0:
            for range_name in result["s_distribution"]:
                count = result["s_distribution"][range_name]["count"]
                result["s_distribution"][range_name]["percentage"] = round(count / total_checked * 100, 1)

        # 권장사항 생성
        for range_name, data in result["s_distribution"].items():
            if data["count"] == 0:
                config = S_RANGES[range_name]
                result["recommendations"].append(
                    f"{config['korean_name']} 항목 추가 필요 ({config['display_name']})"
                )

        if result["discovery_location_issues"]:
            result["recommendations"].append(
                f"발견 장소 패턴 {len(result['discovery_location_issues'])}건 검토 필요 (고장영향 != 발견 장소)"
            )

        # 상태 결정
        if result["recommendations"]:
            result["status"] = "warning"

    except FileNotFoundError:
        return {
            "status": "error",
            "message": f"파일을 찾을 수 없습니다: {file_path}",
            "s_distribution": {},
            "discovery_location_issues": []
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "s_distribution": {},
            "discovery_location_issues": []
        }

    return result


def print_report(result: dict):
    """검증 결과 보고서 출력."""
    print("\n" + "=" * 70)
    print("[VALIDATE] S값 범위 분포 검증 (S=2-5 / S=6-7 / S=8-10)")
    print("기준: 회의 합의 260109 - 고장영향 = 기능 실패의 결과")
    print("=" * 70)

    if result["status"] == "error":
        print(f"[ERROR] {result.get('message', 'Unknown error')}")
        return

    print(f"Total rows: {result['total_rows']}")
    print(f"Checked rows: {result['checked_rows']}")
    print("-" * 70)

    # S값 분포 요약
    print("\n[S값 분포 SUMMARY]")
    print("-" * 50)

    for range_name, data in result["s_distribution"].items():
        config = S_RANGES[range_name]
        status = "OK" if data["count"] > 0 else "MISSING"
        print(f"  {config['display_name']:20} | {data['count']:3} items ({data['percentage']:5.1f}%) | {status}")

        if data["items"]:
            for item in data["items"][:2]:
                print(f"                         -> Row {item['row']}: \"{item['effect']}\" (S={item['s_value']})")

    print("-" * 70)

    # 발견 장소 이슈
    if result["discovery_location_issues"]:
        print("\n[발견 장소 패턴 검출] - 고장영향이 아닌 발견 장소일 수 있음")
        print("-" * 50)
        for issue in result["discovery_location_issues"][:5]:
            print(f"  Row {issue['row']}: \"{issue['effect']}\"")
            print(f"         패턴: {', '.join(issue['patterns'])}")
        if len(result["discovery_location_issues"]) > 5:
            print(f"  ... 외 {len(result['discovery_location_issues']) - 5}건")
        print()
        print("  [참고] 고장영향 = 기능 실패의 결과 (인과관계 필수)")
        print("         '조립 불합격', 'FAT 불합격'은 발견 장소이지 기능 실패 결과가 아님")
        print("-" * 70)

    # 결과
    if result["status"] == "pass":
        print("[PASS] S값 범위 분포가 적절합니다.")
    else:
        print("[WARNING] 검토가 필요합니다!")
        print("\n[RECOMMENDATIONS]")
        for rec in result["recommendations"]:
            print(f"  -> {rec}")
        print("\n[REFERENCE]")
        print("  -> references/failure-effect-phases.md (고장영향 작성 가이드)")
        print("  -> references/column-details.md (컬럼별 정의)")

    print("=" * 70)


def main():
    if len(sys.argv) < 2:
        print("사용법: python validate_lifecycle_coverage.py <excel_file>")
        print("예시: python validate_lifecycle_coverage.py CORE_FMEA.xlsx")
        print()
        print("검증 항목:")
        print("  1. S값 범위별 분포 (S=2-5 / S=6-7 / S=8-10)")
        print("  2. 발견 장소 패턴 검출 (조립 불합격, FAT 불합격 등)")
        print()
        print("기준: 회의 합의 260109")
        print("  - 고장영향 = 기능 실패의 결과 (인과관계 필수)")
        print("  - 발견 시점은 S값으로 반영")
        sys.exit(1)

    file_path = sys.argv[1]
    result = validate_s_distribution(file_path)

    print_report(result)

    print("\n[JSON Output]")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result["status"] == "error":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
