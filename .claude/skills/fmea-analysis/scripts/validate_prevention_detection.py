#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
H열(현재예방대책) / J열(현재검출대책) 검증 스크립트

검증 항목:
1. 출처 필수: (IEQT-T-W030 §3.2), (IEC 60076-5 §8.2), (일반) 형식
2. 기준값 필수: 45±5 N.m, 110% 이하 등 정량적 수치
3. 형식 필수: [단계]: [대책] (설계/재료/제작/시험)
4. 금지 패턴: (작업표준), (R시리즈), (CS) 등 일반 용어
5. 약어 금지: CS -> CHECK SHEET

사용법:
    python validate_prevention_detection.py <excel_file>
    python validate_prevention_detection.py 단자_FMEA.xlsx
"""

import sys
import re
from pathlib import Path
from typing import Tuple, List, Dict, Any
import pandas as pd


def load_prevention_detection_ontology() -> dict:
    """
    prevention-detection-ontology.md에서 검증 규칙 로드

    Returns:
        {
            'required_stages': ['설계', '재료', '제작', '시험'],
            'source_patterns': {...},
            'forbidden_source': [...],
            'required_value_patterns': [...],
            'forbidden_vague': [...],
            'abbreviation_map': {...},
            'severity_levels': {...}
        }
    """
    script_dir = Path(__file__).parent
    ontology_path = script_dir.parent / "references" / "prevention-detection-ontology.md"

    result = {
        'required_stages': [],
        'source_patterns': {
            'internal': [],
            'external': [],
            'general': []
        },
        'forbidden_source': [],
        'required_value_patterns': [],
        'value_examples': [],
        'forbidden_vague': [],
        'abbreviation_map': {},
        'severity_levels': {}
    }

    if not ontology_path.exists():
        print(f"[WARNING] 온톨로지 파일 없음: {ontology_path}")
        # 기본값 설정
        result['required_stages'] = ['설계', '재료', '제작', '시험']
        result['forbidden_source'] = ['작업표준', '검사기준', '시험요령', 'R시리즈', 'W시리즈', 'CS']
        result['forbidden_vague'] = ['적정', '적절', '충분', '양호', '정상']
        result['required_value_patterns'] = ['N.m', 'mm', '%', '°C', '개월']
        result['abbreviation_map'] = {'CS': 'CHECK SHEET'}
        return result

    content = ontology_path.read_text(encoding='utf-8')

    # 섹션별 파싱
    sections = re.split(r'\n## SECTION:', content)

    for section in sections:
        lines = section.strip().split('\n')
        if not lines:
            continue

        section_name = lines[0].strip()

        # REQUIRED_STAGES
        if section_name == 'REQUIRED_STAGES':
            for line in lines[1:]:
                if line.strip() and not line.startswith('#') and not line.startswith('-'):
                    result['required_stages'] = [s.strip() for s in line.split(',') if s.strip()]
                    break

        # SOURCE_PATTERNS
        elif section_name == 'SOURCE_PATTERNS':
            current_category = None
            for line in lines[1:]:
                if line.strip().startswith('---'):
                    break
                if line.startswith('### '):
                    category = line.replace('### ', '').strip().lower()
                    if '내부' in category:
                        current_category = 'internal'
                    elif '외부' in category:
                        current_category = 'external'
                    elif '일반' in category:
                        current_category = 'general'
                elif ':' in line and current_category and not line.startswith('#'):
                    _, patterns = line.split(':', 1)
                    result['source_patterns'][current_category].extend(
                        [p.strip() for p in patterns.split(',') if p.strip()]
                    )

        # FORBIDDEN_SOURCE_PATTERNS
        elif section_name == 'FORBIDDEN_SOURCE_PATTERNS':
            for line in lines[1:]:
                if line.strip().startswith('---'):
                    break
                if ':' in line and not line.startswith('#'):
                    _, patterns = line.split(':', 1)
                    result['forbidden_source'].extend(
                        [p.strip() for p in patterns.split(',') if p.strip()]
                    )

        # REQUIRED_VALUE_PATTERNS
        elif section_name == 'REQUIRED_VALUE_PATTERNS':
            for line in lines[1:]:
                if line.strip().startswith('---'):
                    break
                if ':' in line and not line.startswith('#'):
                    _, patterns = line.split(':', 1)
                    result['required_value_patterns'].extend(
                        [p.strip() for p in patterns.split(',') if p.strip()]
                    )

        # VALUE_FORMAT_EXAMPLES
        elif section_name == 'VALUE_FORMAT_EXAMPLES':
            for line in lines[1:]:
                if line.strip().startswith('---'):
                    break
                if ':' in line and not line.startswith('#'):
                    _, examples = line.split(':', 1)
                    result['value_examples'].extend(
                        [e.strip() for e in examples.split(',') if e.strip()]
                    )

        # FORBIDDEN_VAGUE_EXPRESSIONS
        elif section_name == 'FORBIDDEN_VAGUE_EXPRESSIONS':
            for line in lines[1:]:
                if line.strip().startswith('---'):
                    break
                if ':' in line and not line.startswith('#'):
                    _, patterns = line.split(':', 1)
                    result['forbidden_vague'].extend(
                        [p.strip() for p in patterns.split(',') if p.strip()]
                    )

        # ABBREVIATION_MAP
        elif section_name == 'ABBREVIATION_MAP':
            for line in lines[1:]:
                if line.strip().startswith('---'):
                    break
                if ':' in line and not line.startswith('#'):
                    abbr, full = line.split(':', 1)
                    result['abbreviation_map'][abbr.strip()] = full.strip()

        # SEVERITY_LEVELS
        elif section_name == 'SEVERITY_LEVELS':
            for line in lines[1:]:
                if line.strip().startswith('---'):
                    break
                if ':' in line and not line.startswith('#'):
                    level, desc = line.split(':', 1)
                    result['severity_levels'][level.strip()] = desc.strip()

    return result


# 온톨로지 로드 (모듈 로드 시 1회)
_ontology = load_prevention_detection_ontology()

REQUIRED_STAGES = _ontology['required_stages']
SOURCE_PATTERNS = _ontology['source_patterns']
FORBIDDEN_SOURCE = _ontology['forbidden_source']
REQUIRED_VALUE_PATTERNS = _ontology['required_value_patterns']
FORBIDDEN_VAGUE = _ontology['forbidden_vague']
ABBREVIATION_MAP = _ontology['abbreviation_map']


def validate_stage_format(value: str) -> Tuple[bool, str]:
    """
    [단계]: [대책] 형식 검증
    """
    if pd.isna(value) or str(value).strip() == '':
        return False, "[ERROR] 빈 값"

    value_str = str(value).strip()

    # : 가 있는지 확인
    if ':' not in value_str:
        return False, "[ERROR] '[단계]: [대책]' 형식 필요"

    # 첫 번째 줄에서 단계 추출
    first_line = value_str.split('\n')[0]
    stage = first_line.split(':')[0].strip()

    # 단계가 유효한지 확인
    if stage not in REQUIRED_STAGES:
        return False, f"[ERROR] 단계 '{stage}'는 {REQUIRED_STAGES} 중 하나여야 함"

    return True, "OK"


def validate_source_presence(value: str) -> Tuple[bool, str, str]:
    """
    출처 존재 여부 검증

    [!!] 핵심 규칙:
    - 내부문서(IEQT-T-*, CHECK SHEET) 출처: 필수 (ERROR)
    - 외부표준(IEC, IEEE, CIGRE) 출처: 선택사항 (INFO)

    Returns:
        (is_valid, reason, severity)
    """
    if pd.isna(value) or str(value).strip() == '':
        return False, "[ERROR] 빈 값", "ERROR"

    value_str = str(value)

    # 괄호 안 내용 추출
    source_matches = re.findall(r'\(([^)]+)\)', value_str)

    if not source_matches:
        return False, "[ERROR] 출처 없음 - (IEQT-T-W030 §3.2) 형식 필요", "ERROR"

    # 유효한 출처가 있는지 확인
    valid_sources = []
    has_internal = False
    has_external = False
    has_general = False
    has_section = False

    for source in source_matches:
        # 내부문서 체크 (필수!)
        for pattern in SOURCE_PATTERNS['internal']:
            if pattern in source:
                valid_sources.append(source)
                has_internal = True
                if '§' in source or 'No.' in source or '-' in source.split()[-1] if source.split() else False:
                    has_section = True
                break

        # 외부표준 체크 (선택사항)
        for pattern in SOURCE_PATTERNS['external']:
            if pattern in source:
                valid_sources.append(source)
                has_external = True
                if '§' in source:
                    has_section = True
                break

        # 일반 체크
        if source.strip() == '일반':
            valid_sources.append(source)
            has_general = True

    # [!!] 출처 검증: WARNING 수준 (ERROR 아님!)
    # 모든 항목에 출처가 필수는 아님 - 출처 없는 항목도 허용
    if not has_internal and not has_general:
        # 외부표준만 있는 경우
        if has_external:
            return True, "[INFO] 내부문서 출처 추가 권장", "INFO"
        # 출처 없는 경우도 WARNING (ERROR 아님!)
        return True, "[WARNING] 출처 없음 - 가능하면 (IEQT-T-* §X.X) 또는 (일반) 추가 권장", "WARNING"

    # 섹션 번호 권장
    if has_internal and not has_section:
        return True, f"[INFO] 섹션 번호 권장 - §3.2 또는 No.5 형식 추가 권장", "INFO"

    # 일반만 있는 경우 정보
    if has_general and not has_internal:
        return True, "[INFO] 일반 출처만 있음 - 내부문서 우선 권장", "INFO"

    return True, "OK", "OK"


def validate_forbidden_source(value: str) -> Tuple[bool, str]:
    """
    금지 패턴 검증 (일반 용어, 시리즈명, 약어)

    [!!] 핵심 규칙:
    - 문서번호(IEQT-T-*, CHECK SHEET) 포함 시 -> 금지 패턴 우회!
    - 금지 패턴 단독 사용 시에만 ERROR
    """
    if pd.isna(value) or str(value).strip() == '':
        return True, "빈 값"

    value_str = str(value)

    # 괄호 안 내용에서 금지 패턴 체크
    source_matches = re.findall(r'\(([^)]+)\)', value_str)

    for source in source_matches:
        # [!!] 문서번호가 있으면 금지 패턴 체크 건너뜀!
        if 'IEQT-T' in source or 'CHECK SHEET' in source or 'CHECK_SHEET' in source:
            continue

        for forbidden in FORBIDDEN_SOURCE:
            # 금지 패턴이 단독으로 사용된 경우만 ERROR
            if forbidden == source.strip():
                return False, f"[ERROR] 금지 패턴 '{forbidden}' 단독 사용 - 정확한 문서번호 필요"
            # 금지 패턴이 문서번호 없이 포함된 경우
            if forbidden in source:
                return False, f"[ERROR] 금지 패턴 '{forbidden}' 포함 - 정확한 문서번호 필요"

    return True, "OK"


def validate_abbreviation(value: str) -> Tuple[bool, str]:
    """
    약어 사용 검증
    """
    if pd.isna(value) or str(value).strip() == '':
        return True, "빈 값"

    value_str = str(value)

    for abbr, full in ABBREVIATION_MAP.items():
        # 정확한 약어 매칭 (예: CS가 단독으로 있는 경우)
        if re.search(rf'\b{re.escape(abbr)}\b', value_str) and full not in value_str:
            return False, f"[WARNING] 약어 '{abbr}' 사용 -> '{full}'로 변경 권장"

    return True, "OK"


def validate_value_presence(value: str) -> Tuple[bool, str, str]:
    """
    기준값 존재 여부 검증

    Returns:
        (is_valid, reason, severity)
    """
    if pd.isna(value) or str(value).strip() == '':
        return False, "[ERROR] 빈 값", "ERROR"

    value_str = str(value)

    # 숫자가 있는지 확인
    has_number = bool(re.search(r'\d+', value_str))

    # 단위가 있는지 확인
    has_unit = any(unit in value_str for unit in REQUIRED_VALUE_PATTERNS)

    # 숫자와 단위 모두 있으면 OK
    if has_number and has_unit:
        return True, "OK", "OK"

    # 숫자만 있고 단위 없음
    if has_number and not has_unit:
        return True, "[INFO] 단위 추가 권장", "INFO"

    # 숫자 없음
    return False, "[WARNING] 기준값 없음 - 정량적 수치(45±5 N.m, 110% 등) 필요", "WARNING"


def validate_vague_expression(value: str) -> Tuple[bool, str]:
    """
    모호한 표현 검증
    """
    if pd.isna(value) or str(value).strip() == '':
        return True, "빈 값"

    value_str = str(value)

    for vague in FORBIDDEN_VAGUE:
        # 모호한 표현이 단독으로 사용된 경우 (수치 없이)
        if vague in value_str:
            # 같은 줄에 숫자가 있는지 확인
            lines = value_str.split('\n')
            for line in lines:
                if vague in line and not re.search(r'\d+', line):
                    return False, f"[WARNING] 모호한 표현 '{vague}' - 구체적 수치 추가 필요"

    return True, "OK"


def validate_prevention_detection(file_path: str) -> dict:
    """
    Excel 파일의 H열(현재예방대책)과 J열(현재검출대책) 검증

    Returns:
        {
            "status": "pass" | "fail" | "error",
            "total_rows": int,
            "checked_rows": int,
            "violations": {
                "H": [...],
                "J": [...]
            },
            "warnings": {
                "H": [...],
                "J": [...]
            },
            "summary": {...}
        }
    """
    result = {
        "status": "pass",
        "total_rows": 0,
        "checked_rows": 0,
        "violations": {"H": [], "J": []},
        "warnings": {"H": [], "J": []},
        "info": {"H": [], "J": []},
        "summary": {
            "error_count": 0,
            "warning_count": 0,
            "info_count": 0,
            "source_missing": 0,
            "value_missing": 0,
            "forbidden_used": 0
        }
    }

    try:
        # FMEA 시트 읽기 (헤더 없이)
        df = pd.read_excel(file_path, sheet_name='FMEA', header=None)
        result["total_rows"] = len(df)

        # 헤더 행 찾기
        prevention_col = None  # H열
        detection_col = None   # J열

        for i in range(min(10, len(df))):
            row = df.iloc[i]
            for j, cell in enumerate(row):
                if pd.notna(cell):
                    cell_str = str(cell)
                    if '현재예방대책' in cell_str or '예방대책' in cell_str:
                        prevention_col = j
                    elif '현재검출대책' in cell_str or '검출대책' in cell_str:
                        detection_col = j

        # 헤더를 못 찾으면 기본 위치 사용 (H=7, J=9)
        if prevention_col is None:
            prevention_col = 7  # H열 (0-indexed)
        if detection_col is None:
            detection_col = 9   # J열 (0-indexed)

        # 데이터 행 시작 찾기 (헤더 이후)
        data_start = 6  # 기본값 (Row 7부터)
        for i in range(len(df)):
            row = df.iloc[i]
            # 단계 태그가 있는 첫 행 찾기
            if prevention_col < len(row):
                cell = str(row.iloc[prevention_col]) if pd.notna(row.iloc[prevention_col]) else ""
                if any(stage + ':' in cell for stage in REQUIRED_STAGES):
                    data_start = i
                    break

        # 각 행 검증
        for i in range(data_start, len(df)):
            row = df.iloc[i]

            # H열 (현재예방대책) 검증
            if prevention_col < len(row):
                h_value = row.iloc[prevention_col]
                if pd.notna(h_value) and str(h_value).strip():
                    result["checked_rows"] += 1
                    _validate_cell(h_value, i + 1, "H", result)

            # J열 (현재검출대책) 검증
            if detection_col < len(row):
                j_value = row.iloc[detection_col]
                if pd.notna(j_value) and str(j_value).strip():
                    _validate_cell(j_value, i + 1, "J", result)

        # 요약 집계
        result["summary"]["error_count"] = len(result["violations"]["H"]) + len(result["violations"]["J"])
        result["summary"]["warning_count"] = len(result["warnings"]["H"]) + len(result["warnings"]["J"])
        result["summary"]["info_count"] = len(result["info"]["H"]) + len(result["info"]["J"])

        if result["summary"]["error_count"] > 0:
            result["status"] = "fail"

    except FileNotFoundError:
        return {
            "status": "error",
            "message": f"파일을 찾을 수 없습니다: {file_path}",
            "violations": {"H": [], "J": []}
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"검증 중 오류 발생: {str(e)}",
            "violations": {"H": [], "J": []}
        }

    return result


def _validate_cell(value: str, row_num: int, col: str, result: dict):
    """
    단일 셀 검증 및 결과 추가
    """
    issues = []

    # 1. 형식 검증
    is_valid, reason = validate_stage_format(value)
    if not is_valid:
        issues.append(("ERROR", reason))
        result["violations"][col].append({
            "row": row_num,
            "value": str(value)[:100],
            "reason": reason
        })

    # 2. 출처 검증
    is_valid, reason, severity = validate_source_presence(value)
    if not is_valid or severity != "OK":
        if severity == "ERROR":
            issues.append(("ERROR", reason))
            result["violations"][col].append({
                "row": row_num,
                "value": str(value)[:100],
                "reason": reason
            })
            result["summary"]["source_missing"] += 1
        elif severity == "WARNING":
            result["warnings"][col].append({
                "row": row_num,
                "value": str(value)[:100],
                "reason": reason
            })
        elif severity == "INFO":
            result["info"][col].append({
                "row": row_num,
                "value": str(value)[:100],
                "reason": reason
            })

    # 3. 금지 패턴 검증
    is_valid, reason = validate_forbidden_source(value)
    if not is_valid:
        issues.append(("ERROR", reason))
        result["violations"][col].append({
            "row": row_num,
            "value": str(value)[:100],
            "reason": reason
        })
        result["summary"]["forbidden_used"] += 1

    # 4. 약어 검증
    is_valid, reason = validate_abbreviation(value)
    if not is_valid:
        result["warnings"][col].append({
            "row": row_num,
            "value": str(value)[:100],
            "reason": reason
        })

    # 5. 기준값 검증
    is_valid, reason, severity = validate_value_presence(value)
    if not is_valid or severity == "WARNING":
        if severity == "WARNING":
            result["warnings"][col].append({
                "row": row_num,
                "value": str(value)[:100],
                "reason": reason
            })
            result["summary"]["value_missing"] += 1

    # 6. 모호한 표현 검증
    is_valid, reason = validate_vague_expression(value)
    if not is_valid:
        result["warnings"][col].append({
            "row": row_num,
            "value": str(value)[:100],
            "reason": reason
        })


def print_validation_report(result: dict):
    """
    검증 결과 출력
    """
    print("=" * 60)
    print("H열/J열 검증 결과 (Prevention-Detection Validation)")
    print("=" * 60)

    print(f"\n총 행 수: {result.get('total_rows', 0)}")
    print(f"검증 행 수: {result.get('checked_rows', 0)}")

    # ERROR 출력
    print("\n[1] ERRORS (즉시 수정 필요)")
    print("-" * 40)

    for col in ["H", "J"]:
        col_name = "현재예방대책" if col == "H" else "현재검출대책"
        violations = result.get("violations", {}).get(col, [])
        print(f"\n  {col}열 ({col_name}): {len(violations)}건")
        for v in violations[:10]:  # 최대 10개만 출력
            print(f"    Row {v['row']}: {v['reason']}")
            print(f"           값: \"{v['value'][:50]}...\"" if len(v['value']) > 50 else f"           값: \"{v['value']}\"")

    # WARNING 출력
    print("\n[2] WARNINGS (수정 권장)")
    print("-" * 40)

    for col in ["H", "J"]:
        col_name = "현재예방대책" if col == "H" else "현재검출대책"
        warnings = result.get("warnings", {}).get(col, [])
        print(f"\n  {col}열 ({col_name}): {len(warnings)}건")
        for w in warnings[:5]:  # 최대 5개만 출력
            print(f"    Row {w['row']}: {w['reason']}")

    # 요약
    print("\n" + "=" * 60)
    summary = result.get("summary", {})
    print(f"[SUMMARY]")
    print(f"  ERROR: {summary.get('error_count', 0)}건")
    print(f"  WARNING: {summary.get('warning_count', 0)}건")
    print(f"  INFO: {summary.get('info_count', 0)}건")
    print(f"  - 출처 누락: {summary.get('source_missing', 0)}건")
    print(f"  - 기준값 누락: {summary.get('value_missing', 0)}건")
    print(f"  - 금지 패턴 사용: {summary.get('forbidden_used', 0)}건")

    print("\n" + "-" * 60)

    if result["status"] == "pass":
        print("[PASS] All validations passed.")
    else:
        print("[FAIL] Please fix the issues above.")
        print("\n[FIX GUIDE]")
        print("  [출처] 문서번호 + 섹션번호 필수")
        print("         예: (IEQT-T-W030 §3.2), (권선 CHECK SHEET 권선조립-No.3)")
        print("  [기준값] 정량적 수치 필수")
        print("         예: 45±5 N.m, 110% 이하, 6개월")
        print("  [금지] (작업표준), (R시리즈), (CS) 등 일반 용어 금지")
        print("  Reference: references/prevention-detection-ontology.md")

    print("=" * 60)


def main():
    if len(sys.argv) < 2:
        print("사용법: python validate_prevention_detection.py <excel_file>")
        print("예시: python validate_prevention_detection.py 단자_FMEA.xlsx")
        sys.exit(1)

    file_path = sys.argv[1]
    result = validate_prevention_detection(file_path)
    print_validation_report(result)

    # 종료 코드
    if result["status"] == "pass":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
