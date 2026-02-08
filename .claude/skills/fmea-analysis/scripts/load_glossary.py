# -*- coding: utf-8 -*-
"""
용어집 로더 스크립트
변압기_전문용어집_V2.2.xlsx에서 표준 용어를 로드

사용법:
    from load_glossary import load_glossary, normalize_term

    glossary = load_glossary()
    normalized = normalize_term("스텝랩", glossary)  # -> "STEP LAP"
"""

import sys
import io
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, List

# Windows cp949 인코딩 문제 해결
try:
    if sys.stdout and hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass  # 이미 처리됨

# 용어집 파일 경로 (SSOT) - 상대 경로 사용
# 프로젝트 루트: 35_FMEA/
GLOSSARY_EXCEL_PATH = Path("01.회의/00.회의 자료/01.용어정리/변압기_전문용어집_V2.2.xlsx")


def load_glossary(excel_path: Optional[Path] = None) -> Dict:
    """
    용어집 Excel에서 표준 용어 로드

    Returns:
        {
            'terms': {
                '표준용어': {
                    'standard': '표준용어',
                    'korean': '한글용어',
                    'english': '영문용어',
                    'aliases': ['별칭1', '별칭2'],
                    'definition': '정의',
                    'category': '카테고리',
                    'source': '출처'
                }
            },
            'alias_map': {  # 별칭 -> 표준용어 매핑
                '별칭1': '표준용어',
                '한글용어': '표준용어',
                ...
            }
        }
    """
    if excel_path is None:
        excel_path = GLOSSARY_EXCEL_PATH

    result = {
        'terms': {},
        'alias_map': {}
    }

    if not excel_path.exists():
        print(f"[WARN] 용어집 파일 없음: {excel_path}")
        return result

    try:
        # Excel 읽기 (2행이 헤더, 0-indexed)
        df = pd.read_excel(excel_path, header=2)

        # 컬럼명 정리
        df.columns = ['구분', '표준용어', '한글용어', '영문용어', '별칭', '정의', '출처', '업무분야', '카테고리', '비고']

        # 유효한 데이터만 필터링
        df = df[df['표준용어'].notna()]
        df = df[df['표준용어'].astype(str).str.strip() != '']
        df = df[df['표준용어'].astype(str).str.strip() != '표준 용어']  # 헤더 행 제외

        for _, row in df.iterrows():
            std_term = str(row['표준용어']).strip()
            korean = str(row['한글용어']).strip() if pd.notna(row['한글용어']) else ''
            english = str(row['영문용어']).strip() if pd.notna(row['영문용어']) else ''
            aliases_raw = str(row['별칭']).strip() if pd.notna(row['별칭']) else ''
            definition = str(row['정의']).strip() if pd.notna(row['정의']) else ''
            category = str(row['카테고리']).strip() if pd.notna(row['카테고리']) else ''
            source = str(row['출처']).strip() if pd.notna(row['출처']) else ''

            # 별칭 파싱 (쉼표로 구분)
            aliases = [a.strip() for a in aliases_raw.split(',') if a.strip()]

            # 표준용어 저장
            result['terms'][std_term] = {
                'standard': std_term,
                'korean': korean,
                'english': english,
                'aliases': aliases,
                'definition': definition,
                'category': category,
                'source': source
            }

            # 별칭 -> 표준용어 매핑 생성
            # 한글용어가 표준용어와 다르면 매핑 추가
            if korean and korean != std_term:
                result['alias_map'][korean] = std_term
                result['alias_map'][korean.lower()] = std_term

            # 영문용어 매핑
            if english and english != std_term:
                result['alias_map'][english] = std_term
                result['alias_map'][english.lower()] = std_term
                result['alias_map'][english.upper()] = std_term

            # 별칭들 매핑
            for alias in aliases:
                if alias != std_term:
                    result['alias_map'][alias] = std_term
                    result['alias_map'][alias.lower()] = std_term
                    result['alias_map'][alias.upper()] = std_term

        print(f"[OK] 용어집 로드 완료: {len(result['terms'])}개 표준용어, {len(result['alias_map'])}개 별칭 매핑")

    except Exception as e:
        print(f"[ERROR] 용어집 로드 실패: {e}")

    return result


def normalize_term(text: str, glossary: Dict) -> str:
    """
    텍스트 내의 비표준 용어를 표준 용어로 변환

    Args:
        text: 변환할 텍스트
        glossary: load_glossary()로 로드한 용어집

    Returns:
        표준 용어로 변환된 텍스트
    """
    if not text or not isinstance(text, str):
        return text

    result = text
    alias_map = glossary.get('alias_map', {})

    # 긴 별칭부터 처리 (부분 매칭 방지)
    sorted_aliases = sorted(alias_map.keys(), key=len, reverse=True)

    for alias in sorted_aliases:
        if alias in result:
            standard = alias_map[alias]
            # 이미 표준용어로 되어있으면 스킵
            if standard not in result:
                result = result.replace(alias, standard)

    return result


def get_standard_term(term: str, glossary: Dict) -> Optional[str]:
    """
    주어진 용어의 표준 용어 반환

    Args:
        term: 찾을 용어 (표준/별칭/한글/영문)
        glossary: load_glossary()로 로드한 용어집

    Returns:
        표준 용어 또는 None (찾지 못한 경우)
    """
    term = term.strip()

    # 이미 표준용어인 경우
    if term in glossary.get('terms', {}):
        return term

    # 별칭에서 찾기
    alias_map = glossary.get('alias_map', {})
    return alias_map.get(term) or alias_map.get(term.lower()) or alias_map.get(term.upper())


def print_glossary_summary(glossary: Dict):
    """용어집 요약 출력"""
    terms = glossary.get('terms', {})

    print("\n" + "=" * 60)
    print("용어집 요약 (변압기_전문용어집_V2.2.xlsx)")
    print("=" * 60)

    # 카테고리별 분류
    categories = {}
    for term, info in terms.items():
        cat = info.get('category', '미분류')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(term)

    print(f"\n총 용어 수: {len(terms)}개")
    print(f"총 별칭 매핑: {len(glossary.get('alias_map', {}))}개")
    print("\n카테고리별 분포:")
    for cat, term_list in sorted(categories.items()):
        print(f"  {cat}: {len(term_list)}개")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    # 테스트
    glossary = load_glossary()
    print_glossary_summary(glossary)

    # 샘플 변환 테스트
    print("\n=== 변환 테스트 ===")
    test_cases = [
        "스텝랩 조립",
        "권선조립 공정",
        "DGA 분석 결과",
    ]
    for test in test_cases:
        normalized = normalize_term(test, glossary)
        if test != normalized:
            print(f"  '{test}' -> '{normalized}'")
        else:
            print(f"  '{test}' (변환 없음)")
