# -*- coding: utf-8 -*-
"""
고장영향(C열) 검증 스크립트
FMEA Excel 생성 시 GATE 4에서 사용

사용법:
    python validate_failure_effect.py <excel_file>
    python validate_failure_effect.py 철심_FMEA.xlsx

반환:
    - 검증 통과: exit code 0, JSON {"status": "pass", "violations": []}
    - 검증 실패: exit code 1, JSON {"status": "fail", "violations": [...]}

검증 항목:
    1. 금지어 검증: 검사/판정 결과(FAT 불합격, 조립불합격 등)는 고장영향이 아님
    2. 기능-고장영향 인과관계 검증: 기능 동사와 고장영향의 논리적 연결 확인
       (diamond-structure.md 기능 동사 -> 허용/금지 고장영향 매핑 기준)
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

# 금지어: 검사/판정 결과 (정확히 일치 또는 포함)
FORBIDDEN_INSPECTION_RESULTS = [
    # FAT/검사 관련
    'FAT 불합격', 'FAT불합격', 'FAT 실패', 'FAT실패',
    # 공정별 불합격
    '조립불합격', '조립 불합격', '용접불합격', '용접 불합격',
    '외관불합격', '외관 불합격', '도장불합격', '도장 불합격',
    '기능검사 불합격', '기능검사불합격',
    # 일반 판정 결과
    '불합격', '합격', '부적합', '적합',
    'NG', 'OK', 'FAIL', 'PASS', 'Fail', 'Pass',
    '양호', '불량',
    # 시험 관련
    'SAT 불합격', 'SAT불합격',
]

# 금지 패턴: 공정명 + 판정결과 조합
FORBIDDEN_PROCESS_PATTERNS = [
    # 공정명이 단독으로 오는 경우는 허용하지만,
    # "불합격", "합격" 등과 조합되면 금지
]

# ============================================================
# 기능-고장영향 인과관계 검증
# Single Source of Truth: references/diamond-structure.md
# 온톨로지 확장: references/effect-ontology.md
# ============================================================

def load_effect_ontology() -> dict:
    """
    effect-ontology.md에서 키워드 온톨로지 로드 (v2.0)

    C열(고장영향)에 물리적 상태(E열 내용) 금지 규칙 로드
    기능 동사별 금지 키워드 확장

    Returns:
        {
            "keyword_expansion": {"소음": ["소음", "이상음", ...], ...},
            "forbidden_physical": ["변형", "크랙", "탈락", "이완", ...]
        }
    """
    result = {
        "keyword_expansion": {},
        "forbidden_physical": []  # v2.0: forbidden_visible -> forbidden_physical
    }
    script_dir = Path(__file__).parent
    ontology_path = script_dir.parent / "references" / "effect-ontology.md"

    if not ontology_path.exists():
        print(f"[INFO] effect-ontology.md not found, using basic matching")
        return result

    try:
        with open(ontology_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # SECTION:FORBIDDEN_PHYSICAL_IN_EFFECT 파싱 (v2.0 새 형식)
        # 형식: 카테고리명: 키워드1, 키워드2, ...
        sections = re.split(r'\n## SECTION:', content)
        for section in sections:
            lines = section.strip().split('\n')
            if not lines:
                continue

            section_name = lines[0].strip()

            # v2.0 새 섹션명
            if section_name == 'FORBIDDEN_PHYSICAL_IN_EFFECT':
                for line in lines[1:]:
                    if line.strip().startswith('---'):
                        break
                    # "카테고리명: 키워드1, 키워드2" 형식 파싱
                    if ':' in line and not line.startswith('#') and not line.startswith('>'):
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            keywords = parts[1].strip()
                            result['forbidden_physical'].extend(
                                [k.strip() for k in keywords.split(',') if k.strip()]
                            )

            # 하위 호환: 구버전 섹션명도 지원
            elif section_name == 'FORBIDDEN_VISIBLE_IN_EFFECT':
                for line in lines[1:]:
                    if line.strip().startswith('---'):
                        break
                    if ':' in line and not line.startswith('#') and not line.startswith('>'):
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            keywords = parts[1].strip()
                            result['forbidden_physical'].extend(
                                [k.strip() for k in keywords.split(',') if k.strip()]
                            )

        # 테이블 행 파싱: | **키워드** | 관련어1, 관련어2 |
        # 헤더 행 제외: "기본 키워드", "관련어" 등은 스킵
        table_pattern = r'\|\s*\*\*(\w+)\*\*\s*\|([^|]+)\|'
        header_keywords = {'기본', '키워드', '관련어'}

        for match in re.finditer(table_pattern, content):
            base_keyword = match.group(1).strip()

            # 헤더 행 스킵
            if base_keyword in header_keywords:
                continue

            related_raw = match.group(2).strip()

            # 쉼표로 분리하고 정리
            related = [item.strip() for item in related_raw.split(',') if item.strip()]

            # 기본 키워드도 관련어에 포함
            if base_keyword not in related:
                related.insert(0, base_keyword)

            result['keyword_expansion'][base_keyword] = related

        # 중복 제거
        result['forbidden_physical'] = list(set(result['forbidden_physical']))

    except Exception as e:
        print(f"[WARN] Failed to parse effect-ontology.md: {e}")

    return result


def expand_forbidden_keywords(base_keywords: list, ontology: dict) -> set:
    """
    온톨로지를 사용하여 금지 키워드 확장

    Args:
        base_keywords: diamond-structure.md의 기본 금지 키워드 (예: ["소음", "외관"])
        ontology: load_effect_ontology()에서 로드한 온톨로지 (keyword_expansion 딕셔너리)

    Returns:
        확장된 금지 키워드 집합 (예: {"소음", "이상음", "소음 기준 초과", "외관", "외관 품질 저하", ...})
    """
    expanded = set()

    # ontology가 새 형식인지 확인
    keyword_expansion = ontology.get('keyword_expansion', ontology) if isinstance(ontology, dict) else ontology

    for keyword in base_keywords:
        # 기본 키워드 항상 추가
        expanded.add(keyword)

        # 온톨로지에서 관련어 확장
        if keyword in keyword_expansion:
            expanded.update(keyword_expansion[keyword])

    return expanded


def validate_physical_in_effect(value: str, forbidden_physical: list) -> Tuple[bool, str]:
    """
    C열(고장영향)에 물리적 상태/변화가 있는지 검증 (v2.0)

    물리적 상태(변형, 크랙, 탈락, 이완 등)는 E열(고장형태)에 배치해야 함!
    C열에는 기능 실패의 결과(통전 불가, 과열, 지락사고 등)만 작성

    Returns:
        (is_valid, reason)
    """
    if pd.isna(value) or str(value).strip() == '':
        return True, "빈 값"

    # 옵션 A: 괄호 안 설명 제거 후 메인 내용만 검증
    value_str = extract_main_content_effect(value)

    if not value_str:
        return True, "빈 값"

    # 물리적 상태 체크
    for physical in forbidden_physical:
        if physical in value_str:
            return False, f"[X] '{physical}'는 물리적 상태 -> E열(고장형태)로 이동! C열에는 기능 실패 결과 작성"

    return True, "OK"


# 하위 호환: 구버전 함수명 유지
def validate_visible_in_effect(value: str, forbidden_visible: list) -> Tuple[bool, str]:
    """하위 호환용 - validate_physical_in_effect 사용 권장"""
    return validate_physical_in_effect(value, forbidden_visible)


def load_function_effect_map() -> dict:
    """
    diamond-structure.md에서 기능 동사 -> 허용/금지 고장영향 매핑 로드

    파싱 대상 테이블 형식 (Line 38-47):
    | 기능 동사 | 기능 실패 의미 | 허용 고장영향 | 금지 고장영향 |
    |----------|--------------|--------------|--------------|
    | **최소화한다** | 최소화 실패 = 증가 | 증가, 상승, 초과 | 소음, 외관, 접지 |

    Returns:
        {"최소화": {"허용": [...], "금지": [...]}, ...}
    """
    mapping = {}
    script_dir = Path(__file__).parent
    md_path = script_dir.parent / "references" / "diamond-structure.md"

    if not md_path.exists():
        print(f"[WARN] diamond-structure.md not found: {md_path}")
        return mapping

    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 테이블 행 파싱: | **동사한다** | ... | 허용1, 허용2 | 금지1, 금지2 |
        # 패턴: | **동사한다** | ... | 허용 | 금지 |
        table_pattern = r'\|\s*\*\*(\w+)한다\*\*\s*\|[^|]+\|([^|]+)\|([^|]+)\|'

        for match in re.finditer(table_pattern, content):
            verb = match.group(1).strip()
            allowed_raw = match.group(2).strip()
            forbidden_raw = match.group(3).strip()

            # 쉼표로 분리하고 정리
            allowed = [item.strip() for item in allowed_raw.split(',') if item.strip()]
            forbidden = [item.strip() for item in forbidden_raw.split(',') if item.strip()]

            mapping[verb] = {
                '허용': allowed,
                '금지': forbidden
            }

    except Exception as e:
        print(f"[WARN] Failed to parse diamond-structure.md: {e}")

    return mapping


# 기능 동사 추출 패턴 (동적 생성)
def get_function_verb_patterns(verbs: list) -> list:
    """매핑된 동사 목록으로 추출 패턴 생성"""
    if not verbs:
        return []
    verb_group = '|'.join(verbs)
    return [
        rf'({verb_group})한다',
        rf'({verb_group})하다',
        rf'를?\s*({verb_group})',
        rf'을?\s*({verb_group})',
    ]


def extract_function_verb(function_text: str, patterns: list) -> Optional[str]:
    """
    기능 텍스트에서 동사 추출

    예시:
        "자속 경로를 제공한다" -> "제공"
        "손실을 최소화한다" -> "최소화"
    """
    if pd.isna(function_text) or str(function_text).strip() == '':
        return None

    text = str(function_text).strip()

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)

    return None


def extract_main_content_effect(value: str) -> str:
    """
    옵션 A 형식에서 괄호 안 설명을 제거하고 메인 내용만 추출 (고장영향용)

    예: "전압 변환 불가\n(자속 밀도 저하로 2차측 출력 불가)" -> "전압 변환 불가"
    예: "전압 변환 불가(설명)" -> "전압 변환 불가"
    """
    if pd.isna(value) or str(value).strip() == '':
        return ''

    value_str = str(value).strip()

    # 줄바꿈이 있으면 첫 줄만 추출
    if '\n' in value_str:
        value_str = value_str.split('\n')[0].strip()

    # 괄호 안 내용 제거 (끝에 있는 괄호)
    import re
    value_str = re.sub(r'\([^)]*\)$', '', value_str).strip()

    return value_str


def validate_function_effect_relation(function_text: str, effect_text: str,
                                       mapping: dict, patterns: list,
                                       ontology: dict = None) -> Tuple[bool, str]:
    """
    기능-고장영향 인과관계 검증 (온톨로지 확장 지원)
    옵션 A 형식 지원: 괄호 안 설명은 검증 대상에서 제외

    Args:
        function_text: 기능 텍스트
        effect_text: 고장영향 텍스트
        mapping: 기능 동사 -> 허용/금지 매핑
        patterns: 동사 추출 패턴
        ontology: 금지 키워드 확장용 온톨로지 (optional)

    Returns:
        (is_valid, reason)
    """
    if pd.isna(function_text) or pd.isna(effect_text):
        return True, "빈 값"

    function_str = str(function_text).strip()
    # 옵션 A: 괄호 안 설명 제거 후 메인 내용만 검증
    effect_str = extract_main_content_effect(effect_text)

    if not function_str or not effect_str:
        return True, "빈 값"

    # 기능 동사 추출
    verb = extract_function_verb(function_str, patterns)
    if verb is None:
        return True, "동사 미식별 (검증 스킵)"

    # 매핑 테이블에서 규칙 조회
    if verb not in mapping:
        return True, f"동사 '{verb}' 매핑 없음 (검증 스킵)"

    rules = mapping[verb]
    base_forbidden = rules['금지']

    # 온톨로지로 금지 키워드 확장
    if ontology:
        expanded_forbidden = expand_forbidden_keywords(base_forbidden, ontology)
    else:
        expanded_forbidden = set(base_forbidden)

    # 금지 키워드 체크 (확장된 키워드 사용)
    for forbidden in expanded_forbidden:
        if forbidden in effect_str:
            # 기본 키워드인지 확장 키워드인지 구분
            base_match = forbidden in base_forbidden
            if base_match:
                return False, f"'{verb}한다' 기능에 '{forbidden}' 고장영향 부적합 - 별개 기능의 고장영향!"
            else:
                # 확장 키워드로 매칭된 경우, 원본 기본 키워드 찾기
                matched_base = None
                for base in base_forbidden:
                    if ontology and base in ontology and forbidden in ontology[base]:
                        matched_base = base
                        break
                return False, f"'{verb}한다' 기능에 '{forbidden}' 고장영향 부적합 ('{matched_base}' 관련) - 별개 기능의 고장영향!"

    return True, "OK"


def validate_failure_effect(value: str) -> Tuple[bool, str]:
    """
    단일 고장영향 값 검증
    옵션 A 형식 지원: 괄호 안 설명은 검증 대상에서 제외

    Returns:
        (is_valid, reason)
    """
    if pd.isna(value) or str(value).strip() == '':
        return True, "빈 값"

    # 옵션 A: 괄호 안 설명 제거 후 메인 내용만 검증
    value_str = extract_main_content_effect(value)

    if not value_str:
        return True, "빈 값"

    # 금지어 검사 (검사/판정 결과)
    for forbidden in FORBIDDEN_INSPECTION_RESULTS:
        if forbidden in value_str:
            return False, f"검사/판정 결과는 고장영향이 아님: '{forbidden}' -> 기술적 영향으로 변경 필요"

    return True, "OK"


def validate_excel_file(file_path: str) -> dict:
    """
    Excel 파일의 고장영향 열 전체 검증

    검증 항목:
    1. 금지어 검증 (검사/판정 결과)
    2. 기능-고장영향 인과관계 검증

    Returns:
        {
            "status": "pass" | "fail",
            "total_rows": int,
            "violations": [...],
            "causality_violations": [...]
        }
    """
    result = {
        "status": "pass",
        "total_rows": 0,
        "checked_rows": 0,
        "violations": [],           # 금지어 위반
        "causality_violations": [], # 인과관계 위반
        "visible_violations": [],   # 눈에 보이는 현상 위반 (C열에 E열 내용)
        "verb_coverage": {},        # 동사 분포
        "ontology_keywords": 0      # 온톨로지 확장 키워드 수
    }

    # 인과관계 매핑 및 온톨로지 로드
    function_effect_map = load_function_effect_map()
    verb_patterns = get_function_verb_patterns(list(function_effect_map.keys()))
    effect_ontology = load_effect_ontology()

    # 새 형식의 온톨로지에서 데이터 추출 (v2.0)
    keyword_expansion = effect_ontology.get('keyword_expansion', {})
    forbidden_physical = effect_ontology.get('forbidden_physical', [])

    if not function_effect_map:
        print("[WARN] Function-effect mapping not loaded. Causality check skipped.")

    if keyword_expansion:
        total_expanded = sum(len(v) for v in keyword_expansion.values())
        print(f"[INFO] Effect ontology loaded: {len(keyword_expansion)} base keywords -> {total_expanded} expanded")
        result["ontology_keywords"] = total_expanded
    else:
        print("[INFO] No keyword ontology loaded, using basic keyword matching")

    if forbidden_physical:
        print(f"[INFO] Forbidden physical states loaded: {len(forbidden_physical)} keywords")
    else:
        print("[INFO] No forbidden physical list loaded")

    try:
        # FMEA 시트 읽기 (헤더 없이)
        df = pd.read_excel(file_path, sheet_name='FMEA', header=None)
        result["total_rows"] = len(df)

        # 헤더 행 찾기 (기능, 고장영향 열 위치 확인)
        function_col = None
        failure_effect_col = None
        header_row = None

        for i in range(min(10, len(df))):
            row = df.iloc[i]
            for j, val in enumerate(row):
                val_str = str(val).strip()
                if val_str == '기능':
                    function_col = j
                    header_row = i
                elif val_str == '고장영향':
                    failure_effect_col = j

        if failure_effect_col is None:
            return {
                "status": "error",
                "message": "고장영향 열을 찾을 수 없습니다.",
                "violations": []
            }

        # 동사 분포 카운트
        verb_counts = {}

        # 병합 셀 처리: 기능 열의 빈 값을 이전 값으로 채움
        if function_col is not None:
            df[function_col] = df[function_col].ffill()

        # 데이터 행 검증 (헤더 다음 행부터)
        for i in range(header_row + 1, len(df)):
            effect_value = df.iloc[i, failure_effect_col]

            if pd.isna(effect_value) or str(effect_value).strip() == '':
                continue

            result["checked_rows"] += 1

            # 1. 금지어 검증
            is_valid, reason = validate_failure_effect(effect_value)
            if not is_valid:
                result["violations"].append({
                    "row": i + 1,
                    "value": str(effect_value),
                    "reason": reason
                })

            # 2. 물리적 상태 검증 (C열에 E열 내용 금지) - v2.0
            if forbidden_physical:
                phys_valid, phys_reason = validate_physical_in_effect(effect_value, forbidden_physical)
                if not phys_valid:
                    result["visible_violations"].append({
                        "row": i + 1,
                        "value": str(effect_value),
                        "reason": phys_reason
                    })

            # 3. 인과관계 검증 (기능 열이 있을 때만)
            if function_col is not None and function_effect_map:
                function_value = df.iloc[i, function_col]

                # 동사 추출 및 카운트
                verb = extract_function_verb(function_value, verb_patterns)
                if verb:
                    verb_counts[verb] = verb_counts.get(verb, 0) + 1

                # 인과관계 검증 (온톨로지 확장 사용)
                is_valid, reason = validate_function_effect_relation(
                    function_value, effect_value, function_effect_map, verb_patterns,
                    keyword_expansion
                )
                if not is_valid:
                    result["causality_violations"].append({
                        "row": i + 1,
                        "function": str(function_value),
                        "effect": str(effect_value),
                        "reason": reason
                    })

        result["verb_coverage"] = verb_counts

        if result["violations"] or result["causality_violations"] or result["visible_violations"]:
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
    print("[VALIDATE] Failure Effect (C column) Validation")
    print("=" * 60)

    if result["status"] == "error":
        print(f"[ERROR] {result.get('message', 'Unknown error')}")
        return

    print(f"Total rows: {result['total_rows']}")
    print(f"Checked rows: {result['checked_rows']}")
    ontology_count = result.get('ontology_keywords', 0)
    if ontology_count > 0:
        print(f"Ontology expansion: {ontology_count} keywords (effect-ontology.md)")
    print("-" * 60)

    # 1. 동사 분포
    print("\n[1] Function Verb Coverage")
    verb_coverage = result.get("verb_coverage", {})
    if verb_coverage:
        for verb, count in sorted(verb_coverage.items(), key=lambda x: -x[1]):
            print(f"    {verb}한다: {count}개")
    else:
        print("    (동사 분포 없음)")

    # 2. 금지어 위반
    print("\n[2] Forbidden Words Check (검사/판정 결과)")
    print(f"    Violations: {len(result['violations'])}")
    if result["violations"]:
        for v in result["violations"]:
            print(f"    Row {v['row']}: \"{v['value']}\"")
            print(f"           -> {v['reason']}")

    # 3. 눈에 보이는 현상 위반 (C열에 E열 내용)
    print("\n[3] Visible Phenomena Check (C열에 E열 내용 금지)")
    visible_violations = result.get("visible_violations", [])
    print(f"    Violations: {len(visible_violations)}")
    if visible_violations:
        for v in visible_violations:
            print(f"    Row {v['row']}: \"{v['value']}\"")
            print(f"           -> {v['reason']}")

    # 4. 인과관계 위반
    print("\n[4] Function-Effect Causality Check")
    causality_violations = result.get("causality_violations", [])
    print(f"    Violations: {len(causality_violations)}")
    if causality_violations:
        for v in causality_violations:
            print(f"    Row {v['row']}:")
            print(f"       기능: \"{v['function']}\"")
            print(f"       고장영향: \"{v['effect']}\"")
            print(f"       -> {v['reason']}")

    print("-" * 60)

    if result["status"] == "pass":
        print("[PASS] All validations passed.")
    else:
        print("[FAIL] Please fix the issues above.")
        print("\n[FIX GUIDE]")
        if result["violations"]:
            print("  [금지어] 검사/판정 결과 -> 기술적 영향으로 변경")
            print("           예: FAT 불합격 -> 과열, 절연파괴")
        if visible_violations:
            print("  [눈에 보이는 현상] C열(고장영향)에서 E열(고장형태)로 이동")
            print("           예: C열 '부품 이완' -> E열 '부족: 이완'")
            print("               C열에는 '고정력 저하'와 같은 기능 손실 작성")
        if causality_violations:
            print("  [인과관계] 기능 동사와 고장영향의 논리적 연결 확인")
            print("             별개 기능의 고장영향이면 -> 새 기능 추가 검토")
        print("  Reference:")
        print("    - diamond-structure.md: 기본 동사-금지 키워드 매핑")
        print("    - effect-ontology.md: 키워드 변형어 확장, C열 금지 현상 목록")

    print("=" * 60)


def main():
    if len(sys.argv) < 2:
        print("사용법: python validate_failure_effect.py <excel_file>")
        print("예시: python validate_failure_effect.py 철심_FMEA.xlsx")
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
