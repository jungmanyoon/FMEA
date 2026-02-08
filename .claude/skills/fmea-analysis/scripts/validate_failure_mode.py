# -*- coding: utf-8 -*-
"""
고장형태(E열) 금지어 검증 스크립트
FMEA Excel 생성 시 GATE 4에서 사용

사용법:
    python validate_failure_mode.py <excel_file>
    python validate_failure_mode.py 철심_FMEA.xlsx

반환:
    - 검증 통과: exit code 0, JSON {"status": "pass", "violations": []}
    - 검증 실패: exit code 1, JSON {"status": "fail", "violations": [...]}

온톨로지:
    - references/failure-mode-ontology.md에서 규칙 동적 로드
    - SSOT: 모든 금지어/태그 규칙은 온톨로지 파일에서 관리
"""

import sys
import io
import json
import re
import pandas as pd
from pathlib import Path
from typing import Tuple

# Windows cp949 인코딩 문제 해결 (공통 모듈 사용)
from encoding_utils import setup_encoding
setup_encoding()

# 스크립트 디렉토리
script_dir = Path(__file__).parent


def load_failure_mode_ontology() -> dict:
    """
    failure-mode-ontology.md에서 검증 규칙 동적 로드

    파일 형식:
        ## SECTION:<섹션명>
        카테고리: 키워드1, 키워드2, ...

        ### TAG:<태그명>
        허용: 키워드1, 키워드2, ...
        금지: 키워드1, 키워드2, ...

    Returns:
        {
            'forbidden_patterns': [...],  # 부분 일치 금지어
            'forbidden_exact': [...],     # 정확 일치 금지어
            'allowed_exceptions': [...],  # 허용 예외
            'required_tags': [...],       # 필수 태그
            'tag_keyword_map': {...}      # 태그별 허용/금지 매핑
        }
    """
    ontology_path = script_dir.parent / "references" / "failure-mode-ontology.md"

    result = {
        'forbidden_patterns': [],
        'forbidden_exact': [],
        'allowed_exceptions': [],
        'required_tags': [],
        'tag_keyword_map': {},
        'mechanism_keywords': [],  # 메커니즘 용어 (G열로 이동 필요)
        'visible_phenomena': [],   # 눈에 보이는 현상 (허용 목록)
        'abstract_to_visible': {}, # 추상적 개념 -> 구체적 현상 변환 매핑
        'visibility_rule': {}      # 눈에 보이는 현상 검증 규칙
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

        # FORBIDDEN_PATTERNS
        if section_name == 'FORBIDDEN_PATTERNS':
            for line in lines[1:]:
                if ':' in line and not line.startswith('#'):
                    _, keywords = line.split(':', 1)
                    result['forbidden_patterns'].extend(
                        [k.strip() for k in keywords.split(',') if k.strip()]
                    )

        # FORBIDDEN_EXACT
        elif section_name == 'FORBIDDEN_EXACT':
            for line in lines[1:]:
                if ':' in line and not line.startswith('#'):
                    _, keywords = line.split(':', 1)
                    result['forbidden_exact'].extend(
                        [k.strip() for k in keywords.split(',') if k.strip()]
                    )

        # ALLOWED_EXCEPTIONS
        elif section_name == 'ALLOWED_EXCEPTIONS':
            for line in lines[1:]:
                if line.strip() and not line.startswith('#'):
                    result['allowed_exceptions'].extend(
                        [k.strip() for k in line.split(',') if k.strip()]
                    )

        # REQUIRED_TAGS
        elif section_name == 'REQUIRED_TAGS':
            for line in lines[1:]:
                if line.strip() and not line.startswith('#'):
                    result['required_tags'].extend(
                        [k.strip() for k in line.split(',') if k.strip()]
                    )

        # TAG_KEYWORD_MAP
        elif section_name == 'TAG_KEYWORD_MAP':
            current_tag = None
            for line in lines[1:]:
                # ### TAG:<태그명> 형식
                tag_match = re.match(r'### TAG:(.+)', line)
                if tag_match:
                    current_tag = tag_match.group(1).strip()
                    result['tag_keyword_map'][current_tag] = {'허용': [], '금지': []}
                elif current_tag and ':' in line:
                    if line.startswith('허용:'):
                        _, keywords = line.split(':', 1)
                        result['tag_keyword_map'][current_tag]['허용'] = [
                            k.strip() for k in keywords.split(',') if k.strip()
                        ]
                    elif line.startswith('금지:'):
                        _, keywords = line.split(':', 1)
                        result['tag_keyword_map'][current_tag]['금지'] = [
                            k.strip() for k in keywords.split(',') if k.strip()
                        ]

        # MECHANISM_KEYWORDS (메커니즘 용어 - G열로 이동 필요)
        elif section_name == 'MECHANISM_KEYWORDS':
            for line in lines[1:]:
                # 섹션 종료 마커에서 중단
                if line.strip().startswith('---'):
                    break
                # 키워드 라인만 파싱 (마크다운 리스트, 헤더, blockquote 제외)
                stripped = line.strip()
                if ':' in line and not stripped.startswith('#') and not stripped.startswith('-') and not stripped.startswith('>') and not stripped.startswith('|'):
                    _, keywords = line.split(':', 1)
                    result['mechanism_keywords'].extend(
                        [k.strip() for k in keywords.split(',') if k.strip()]
                    )

        # VISIBLE_PHENOMENA (눈에 보이는 현상 목록)
        elif section_name == 'VISIBLE_PHENOMENA':
            for line in lines[1:]:
                if line.strip().startswith('---'):
                    break
                if ':' in line and not line.startswith('#'):
                    _, keywords = line.split(':', 1)
                    result['visible_phenomena'].extend(
                        [k.strip() for k in keywords.split(',') if k.strip()]
                    )

        # VISIBILITY_RULE (눈에 보이는 현상 검증 규칙)
        elif section_name == 'VISIBILITY_RULE':
            for line in lines[1:]:
                if line.strip().startswith('---'):
                    break
                if ':' in line and not line.startswith('#'):
                    key, value = line.split(':', 1)
                    result['visibility_rule'][key.strip()] = value.strip()

        # ABSTRACT_TO_VISIBLE_MAP (추상적 개념 -> 구체적 현상 변환)
        elif section_name == 'ABSTRACT_TO_VISIBLE_MAP':
            for line in lines[1:]:
                if line.strip().startswith('---'):
                    break
                if ':' in line and not line.startswith('#'):
                    abstract, visibles = line.split(':', 1)
                    result['abstract_to_visible'][abstract.strip()] = [
                        v.strip() for v in visibles.split(',') if v.strip()
                    ]

    return result


# 온톨로지 로드 (모듈 로드 시 1회)
_ontology = load_failure_mode_ontology()

# 온톨로지에서 로드된 규칙 (하위 호환성 유지)
FORBIDDEN_PATTERNS = _ontology['forbidden_patterns']
FORBIDDEN_EXACT = _ontology['forbidden_exact']
ALLOWED_EXCEPTIONS = _ontology['allowed_exceptions']
REQUIRED_TAGS = _ontology['required_tags']
TAG_KEYWORD_MAP = _ontology['tag_keyword_map']
MECHANISM_KEYWORDS = _ontology['mechanism_keywords']
VISIBLE_PHENOMENA = _ontology['visible_phenomena']
ABSTRACT_TO_VISIBLE = _ontology['abstract_to_visible']
VISIBILITY_RULE = _ontology['visibility_rule']


def extract_main_content(value: str) -> str:
    """
    옵션 A 형식에서 괄호 안 설명을 제거하고 메인 내용만 추출

    예: "부족: 이완\n(철심 판의 누적 팽창으로 조립 불안정)" -> "부족: 이완"
    예: "부족: 이완(설명)" -> "부족: 이완"
    """
    if pd.isna(value) or str(value).strip() == '':
        return ''

    value_str = str(value).strip()

    # 줄바꿈이 있으면 첫 줄만 추출
    if '\n' in value_str:
        value_str = value_str.split('\n')[0].strip()

    # 괄호 안 내용 제거 (마지막 괄호만 - 메인 내용 뒤의 설명)
    # "부족: 이완(설명)" -> "부족: 이완"
    import re
    # 콜론 뒤의 내용에서 괄호 제거
    if ':' in value_str:
        tag_part, content_part = value_str.split(':', 1)
        content_part = re.sub(r'\([^)]*\)$', '', content_part).strip()
        value_str = f"{tag_part}: {content_part}"

    return value_str


def validate_failure_mode(value: str) -> Tuple[bool, str]:
    """
    단일 고장형태 값 검증
    옵션 A 형식 지원: 괄호 안 설명은 검증 대상에서 제외

    Returns:
        (is_valid, reason)
    """
    if pd.isna(value) or str(value).strip() == '':
        return True, "빈 값"

    # 옵션 A: 괄호 안 설명 제거 후 메인 내용만 검증
    value_str = extract_main_content(value)

    if not value_str:
        return True, "빈 값"

    # 예외 항목은 통과
    for exception in ALLOWED_EXCEPTIONS:
        if exception in value_str:
            return True, f"허용 예외: {exception}"

    # 정확히 일치하는 금지어 검사
    for forbidden in FORBIDDEN_EXACT:
        if forbidden == value_str or forbidden in value_str:
            return False, f"금지어 포함: '{forbidden}' (미래결과/측정값 -> C열 또는 G열로 이동)"

    # 패턴 일치 검사
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in value_str:
            return False, f"금지 패턴 포함: '{pattern}' (측정값/추상적 표현)"

    return True, "OK"


def validate_tag_format(value: str) -> Tuple[bool, str]:
    """
    태그 형식 검증 (부족:/과도:/유해: 중 하나 필수)
    옵션 A 형식 지원: 괄호 안 설명은 검증 대상에서 제외
    """
    if pd.isna(value) or str(value).strip() == '':
        return True, "빈 값"

    # 옵션 A: 괄호 안 설명 제거 후 메인 내용만 검증
    value_str = extract_main_content(value)

    if not value_str:
        return True, "빈 값"

    if not any(tag in value_str for tag in REQUIRED_TAGS):
        return False, "태그 없음: 부족:/과도:/유해: 중 하나 필수"

    return True, "OK"


def validate_tag_content_relation(value: str) -> Tuple[bool, str]:
    """
    태그-내용 인과관계 검증
    옵션 A 형식 지원: 괄호 안 설명은 검증 대상에서 제외
    """
    if pd.isna(value) or str(value).strip() == '':
        return True, "빈 값"

    # 옵션 A: 괄호 안 설명 제거 후 메인 내용만 검증
    value_str = extract_main_content(value)

    if not value_str:
        return True, "빈 값"

    # 태그 추출
    tag = None
    content = value_str
    for t in REQUIRED_TAGS:
        if t in value_str:
            tag = t
            content = value_str.split(t, 1)[1].strip() if t in value_str else value_str
            break

    if tag is None:
        return True, "태그 없음 (별도 검증)"

    if tag not in TAG_KEYWORD_MAP:
        return True, "알 수 없는 태그"

    rules = TAG_KEYWORD_MAP[tag]

    # 금지 키워드 체크
    for forbidden in rules['금지']:
        if forbidden in content:
            return False, f"[X] '{tag}'에 '{forbidden}' 부적합 - 태그 재검토 필요"

    return True, "OK"


def validate_visibility(value: str) -> Tuple[bool, str]:
    """
    고장형태가 '눈에 보이는 현상'인지 의미론적 검증

    검증 원칙:
    - 측정 장비 없이 육안 또는 간단한 검사로 확인 가능해야 함
    - 추상적 개념(체결력, 기밀성 등)은 구체적 현상으로 대체 필요

    Returns:
        (is_valid, reason)
    """
    if pd.isna(value) or str(value).strip() == '':
        return True, "빈 값"

    # 옵션 A: 괄호 안 설명 제거 후 메인 내용만 검증
    value_str = extract_main_content(value)

    if not value_str:
        return True, "빈 값"

    # 태그 제거 후 내용만 검사
    content = value_str
    for tag in REQUIRED_TAGS:
        if tag in value_str:
            content = value_str.split(tag, 1)[1].strip()
            break

    # 허용 예외 항목은 통과
    for exception in ALLOWED_EXCEPTIONS:
        if exception in content:
            return True, f"허용 예외: {exception}"

    # 추상적 개념 체크 (ABSTRACT_TO_VISIBLE 매핑에 있는 키)
    for abstract in ABSTRACT_TO_VISIBLE.keys():
        if abstract in content:
            suggestions = ABSTRACT_TO_VISIBLE[abstract]
            return False, f"[X] '{abstract}'는 측정 필요한 추상적 개념 -> '{', '.join(suggestions[:3])}' 등 구체적 현상으로 대체"

    # 눈에 보이는 현상 목록에 있는지 확인 (권장 사항)
    has_visible = any(v in content for v in VISIBLE_PHENOMENA)

    if not has_visible and len(content) > 2:
        # 완전히 새로운 표현인 경우 경고 (강제 금지는 아님)
        return True, f"[WARN] 눈에 보이는 현상인지 확인 필요: '{content}'"

    return True, "OK"


def validate_mechanism_keywords(value: str) -> Tuple[bool, str]:
    """
    메커니즘 용어 검증 (E열에 있으면 안 되는 용어)
    피로, 크리프 등은 G열(고장 메커니즘)로 이동 필요
    옵션 A 형식 지원: 괄호 안 설명은 검증 대상에서 제외
    """
    if pd.isna(value) or str(value).strip() == '':
        return True, "빈 값"

    # 옵션 A: 괄호 안 설명 제거 후 메인 내용만 검증
    value_str = extract_main_content(value)

    if not value_str:
        return True, "빈 값"

    # 태그 제거 후 내용만 검사
    content = value_str
    for tag in REQUIRED_TAGS:
        if tag in value_str:
            content = value_str.split(tag, 1)[1].strip()
            break

    # 메커니즘 용어 체크 (BLOCKING - 작성가이드 V1.2 근거)
    for mechanism in MECHANISM_KEYWORDS:
        if mechanism in content:
            return False, f"[BLOCKING] '{mechanism}'은 메커니즘(과정)! E열(현재 현상) -> G열(메커니즘)로 이동"

    return True, "OK"


def validate_tag_coverage(values: list) -> dict:
    """
    과/부족/유해 분포 검증
    """
    counts = {tag: sum(1 for v in values if pd.notna(v) and tag in str(v)) for tag in REQUIRED_TAGS}
    warnings = []

    if counts['부족:'] == 0:
        warnings.append("[WARN] '부족:' 없음 - 누락 검토 필요")
    if counts['과도:'] == 0:
        warnings.append("[INFO] '과도:' 없음 - 해당 없으면 OK")
    if counts['유해:'] == 0:
        warnings.append("[INFO] '유해:' 없음 - 해당 없으면 OK")

    return {"counts": counts, "warnings": warnings}


def validate_excel_file(file_path: str) -> dict:
    """
    Excel 파일의 고장형태 열 전체 검증

    Returns:
        {
            "status": "pass" | "fail",
            "total_rows": int,
            "violations": [{"row": int, "value": str, "reason": str}, ...]
        }
    """
    result = {
        "status": "pass",
        "total_rows": 0,
        "checked_rows": 0,
        "violations": [],
        "tag_violations": [],
        "mechanism_violations": [],
        "visibility_violations": [],  # 눈에 보이는 현상 위반
        "tag_coverage": {}
    }

    try:
        # FMEA 시트 읽기 (헤더 없이)
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

        # 데이터 행 검증 (헤더 다음 행부터)
        all_values = []
        for i in range(header_row + 1, len(df)):
            value = df.iloc[i, failure_mode_col]

            if pd.isna(value) or str(value).strip() == '':
                continue

            all_values.append(value)
            result["checked_rows"] += 1

            # 기존 금지어 검증
            is_valid, reason = validate_failure_mode(value)
            if not is_valid:
                result["violations"].append({
                    "row": i + 1,
                    "value": str(value),
                    "reason": reason
                })

            # 태그 형식 검증
            tag_valid, tag_reason = validate_tag_format(value)
            if not tag_valid:
                result["tag_violations"].append({
                    "row": i + 1,
                    "value": str(value),
                    "reason": tag_reason
                })

            # 태그-내용 인과관계 검증
            relation_valid, relation_reason = validate_tag_content_relation(value)
            if not relation_valid:
                result["tag_violations"].append({
                    "row": i + 1,
                    "value": str(value),
                    "reason": relation_reason
                })

            # 메커니즘 용어 검증 (E열 -> G열 이동 필요 항목)
            mech_valid, mech_reason = validate_mechanism_keywords(value)
            if not mech_valid:
                result["mechanism_violations"].append({
                    "row": i + 1,
                    "value": str(value),
                    "reason": mech_reason
                })

            # 눈에 보이는 현상 검증 (의미론적 검증)
            vis_valid, vis_reason = validate_visibility(value)
            if not vis_valid:
                result["visibility_violations"].append({
                    "row": i + 1,
                    "value": str(value),
                    "reason": vis_reason
                })

        # 태그 분포 검증
        result["tag_coverage"] = validate_tag_coverage(all_values)

        if result["violations"] or result["tag_violations"] or result["mechanism_violations"] or result["visibility_violations"]:
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
    print("\n" + "=" * 60)
    print("[VALIDATE] Failure Mode (E column) Validation")
    print("=" * 60)

    if result["status"] == "error":
        print(f"[ERROR] {result.get('message', 'Unknown error')}")
        return

    print(f"Total rows: {result['total_rows']}")
    print(f"Checked rows: {result['checked_rows']}")
    print("-" * 60)

    # 금지어 검증 결과
    print("\n[1] Forbidden Words Check")
    print(f"    Violations: {len(result['violations'])}")
    if result["violations"]:
        for v in result["violations"]:
            print(f"    Row {v['row']}: \"{v['value']}\"")
            print(f"           -> {v['reason']}")

    # 태그 검증 결과
    print("\n[2] Tag Format Check (부족:/과도:/유해:)")
    print(f"    Violations: {len(result.get('tag_violations', []))}")
    if result.get("tag_violations"):
        for v in result["tag_violations"]:
            print(f"    Row {v['row']}: \"{v['value']}\"")
            print(f"           -> {v['reason']}")

    # 태그 분포
    print("\n[3] Tag Coverage")
    coverage = result.get("tag_coverage", {})
    counts = coverage.get("counts", {})
    warnings = coverage.get("warnings", [])
    print(f"    부족: {counts.get('부족:', 0)}개")
    print(f"    과도: {counts.get('과도:', 0)}개")
    print(f"    유해: {counts.get('유해:', 0)}개")
    if warnings:
        for w in warnings:
            print(f"    {w}")

    # 메커니즘 용어 검증 결과 [BLOCKING]
    print("\n[4] Mechanism Keywords Check [BLOCKING] (피로/응력집중/크리프 등 -> G열)")
    print(f"    Violations: {len(result.get('mechanism_violations', []))}")
    if result.get("mechanism_violations"):
        for v in result["mechanism_violations"]:
            print(f"    Row {v['row']}: \"{v['value']}\"")
            print(f"           -> {v['reason']}")
        print("    [TIP] 시점 기반 구분: F(과거원인) -> G(과정메커니즘) -> E(현재현상) -> C(미래영향)")

    # 눈에 보이는 현상 검증 결과 (의미론적 검증)
    print("\n[5] Visibility Check (눈에 보이는 현상인가?)")
    print(f"    Violations: {len(result.get('visibility_violations', []))}")
    if result.get("visibility_violations"):
        for v in result["visibility_violations"]:
            print(f"    Row {v['row']}: \"{v['value']}\"")
            print(f"           -> {v['reason']}")

    print("-" * 60)

    if result["status"] == "pass":
        print("[PASS] All validations passed.")
    else:
        print("[FAIL] Please fix the issues above.")
        print("\n[FIX GUIDE]")
        print("  - Tag format: [부족|과도|유해]: [관찰가능현상]")
        print("  - Forbidden words -> Move to C/G column")
        print("  - Mechanism keywords (피로, 크리프 등) -> Move to G column")
        print("  - Tag-content mismatch -> Check if tag matches the phenomenon")
        print("  - Abstract concepts (체결력, 기밀성 등) -> Replace with visible phenomena")
        print("  - Reference: references/failure-mode-ontology.md (ABSTRACT_TO_VISIBLE_MAP)")

    print("=" * 60)


def main():
    if len(sys.argv) < 2:
        print("사용법: python validate_failure_mode.py <excel_file>")
        print("예시: python validate_failure_mode.py 철심_FMEA.xlsx")
        sys.exit(1)

    file_path = sys.argv[1]
    result = validate_excel_file(file_path)

    # 보고서 출력
    print_report(result)

    # JSON 결과 출력 (파이프라인 연동용)
    print("\n[JSON Output]")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 종료 코드
    if result["status"] == "pass":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
