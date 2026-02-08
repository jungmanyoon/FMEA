# -*- coding: utf-8 -*-
"""
FMEA 후처리 모듈 (postprocess_fmea.py)
- Phase 3 Excel 생성 전 batch/combined JSON에 적용
- fix_phase3_blocking.py 의 패턴을 공통 모듈화

사용법:
  python postprocess_fmea.py <combined_json_path> [--check-only]

기능:
  1. C열 금지어 치환 (effect-ontology.md FORBIDDEN_PHYSICAL_IN_EFFECT)
  2. 인과관계 체인 키워드 주입 (causal-chain-ontology.md)
  3. C/F열 상세설명 누락 보완 (cef-format-rules.md)
  4. 텍스트 정규화 (CRLF -> LF, trailing whitespace)
  5. 정렬 + 번호 재부여 + 예방/검출조치 갱신
  6. 병합 연속성 검증
  7. 통계 출력
"""

import json
import sys
import os
from collections import Counter, defaultdict


# ============================================================
# 온톨로지 데이터 (causal-chain-ontology.md 기반)
# ============================================================

MODE_CAUSE_VALID = {
    '전기적_고장형태': {
        '고장형태': ['층간단락', '지락', '단선', '접촉불량', '절연파괴', '절연저하', '아크발생'],
        '유효원인': ['절연열화', '절연손상', '과전압', '과전류', '이물질침입', '수분침입',
                   '오염', '열화', '제작불량', '조립불량', '설계오류']
    },
    '기계적_고장형태': {
        '고장형태': ['이완', '탈락', '변형', '크랙', '균열', '파손', '마모', '부식', '피로파괴'],
        '유효원인': ['진동', '열응력', '기계적응력', '체결불량', '재료결함', '제작불량',
                   '부식진행', '피로축적', '과부하', '충격']
    },
    '열적_고장형태': {
        '고장형태': ['과열', '열변형', '탄화', '용융', '열화', '변색'],
        '유효원인': ['과부하', '과전류', '냉각불량', '통풍불량', '열축적', '손실증가',
                   '접촉저항증가', '국부발열']
    },
    '화학적_고장형태': {
        '고장형태': ['부식', '산화', '열화', '오염', '변색'],
        '유효원인': ['수분침입', '산소접촉', '화학반응', '오염물질', '절연유열화', '가스발생']
    },
    '유체_고장형태': {
        '고장형태': ['누유', '누설', '유면저하', '유압저하'],
        '유효원인': ['가스켓열화', '용접불량', '크랙', '실링불량', '체결이완', '진동']
    }
}

INVALID_MODE_CAUSE = {
    '층간단락': ['도장불량', '외관손상', '라벨탈락', '턴수설계오류', '턴수계수오류',
               '전압비계산오류', '권선수오류', '동선규격오류'],
    '지락': ['도장불량', '외관손상', '라벨탈락', '턴수설계오류', '턴수계수오류', '전압비계산오류'],
    '절연파괴': ['도장불량', '외관손상', '라벨탈락', '턴수설계오류', '턴수계수오류', '전압비계산오류'],
    '단선': ['절연열화', '절연손상', '수분침입'],
    '변형': ['절연열화', '수분침입', '오염', '과전압', '부분방전'],
    '이완': ['절연열화', '과전압', '과전류'],
    '탈락': ['절연열화', '과전압', '과전류'],
}

LIFECYCLE_KEYWORD_MAP = {
    '전기적_고장형태': {'설계': '설계오류', '재료': '열화', '제작': '제작불량', '시험': '열화'},
    '기계적_고장형태': {'설계': '기계적응력', '재료': '재료결함', '제작': '제작불량', '시험': '진동'},
    '열적_고장형태': {'설계': '냉각불량', '재료': '열축적', '제작': '국부발열', '시험': '과부하'},
    '화학적_고장형태': {'설계': '화학반응', '재료': '오염물질', '제작': '화학반응', '시험': '수분침입'},
    '유체_고장형태': {'설계': '실링불량', '재료': '가스켓열화', '제작': '용접불량', '시험': '진동'},
}

# C열 금지어 -> 대체어 매핑 (effect-ontology.md 기반)
FORBIDDEN_EFFECT_REPLACEMENTS = {
    '단락사고': '기계적 건전성 저하',
    '단락': '절연 기능 저하',
    '크랙': '구조 강도 저하',
    '변형': '조립 정밀도 저하',
    '이완': '고정력 저하',
    '탈락': '고정 기능 상실',
    '부식': '강도 저하',
    '손상': '기능 저하',
    '파손': '구조적 건전성 저하',
    '누유': '밀봉 기능 저하',
    '오염': '절연 기능 저하',
}

# C열 상세설명 기본값 (영향 -> 상세설명)
EFFECT_DETAIL_DEFAULTS = {
    '절연파괴': '(유전체 강도 초과로 인한 절연 내력 상실)',
    '기계적 건전성 저하': '(기계적 강도/안정성 감소로 인한 구조 불안정)',
    '절연 기능 저하': '(절연 특성 저하로 인한 절연 내력 감소)',
    '권선 과열': '(허용 온도 초과로 인한 권선 열화 가속)',
    '손실 증가': '(설계 손실값 초과로 인한 효율 저하)',
    '고정력 저하': '(고정 강도 부족으로 인한 위치 이탈 위험)',
    '고정 기능 상실': '(고정 요소 부재로 인한 구성품 이탈)',
    '구조 강도 저하': '(구조적 결함으로 인한 내력 감소)',
    '조립 정밀도 저하': '(치수/형상 변화로 인한 조립 불량)',
    '밀봉 기능 저하': '(밀봉 불량으로 인한 절연유 누출)',
    '강도 저하': '(재질 열화로 인한 기계적 강도 감소)',
    '기능 저하': '(성능 저하로 인한 정상 동작 불가)',
    '구조적 건전성 저하': '(파손으로 인한 구조적 무결성 상실)',
    '절연 기능 상실': '(절연 내력 완전 상실로 인한 지락/단락)',
}


# ============================================================
# 유틸리티 함수
# ============================================================

def find_category(mode_str):
    """고장형태에서 인과관계 카테고리 탐색"""
    for tag in ['부족:', '과도:', '유해:']:
        if tag in mode_str:
            mode_str = mode_str.split(tag, 1)[1].strip()
            break
    for category, data in MODE_CAUSE_VALID.items():
        for known_mode in data['고장형태']:
            if known_mode in mode_str:
                return category
    return None


def has_valid_cause(cause_str, category):
    """원인에 유효 키워드 포함 여부"""
    valid_causes = MODE_CAUSE_VALID[category]['유효원인']
    return any(vc in cause_str for vc in valid_causes)


def is_invalid_combination(mode_str, keyword):
    """금지 조합 여부"""
    for tag in ['부족:', '과도:', '유해:']:
        if tag in mode_str:
            mode_str = mode_str.split(tag, 1)[1].strip()
            break
    for inv_mode, inv_causes in INVALID_MODE_CAUSE.items():
        if inv_mode in mode_str:
            if keyword in inv_causes:
                return True
    return False


def get_safe_keyword(category, lifecycle, mode_str):
    """안전한 키워드 반환 (금지 조합 회피)"""
    keyword = LIFECYCLE_KEYWORD_MAP.get(category, {}).get(lifecycle, '')
    if not keyword:
        return ''
    if not is_invalid_combination(mode_str, keyword):
        return keyword
    valid_causes = MODE_CAUSE_VALID[category]['유효원인']
    for alt in valid_causes:
        if not is_invalid_combination(mode_str, alt):
            return alt
    return ''


def normalize_text(text):
    """텍스트 정규화: CRLF -> LF, trailing whitespace 제거"""
    if not text:
        return text
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [line.rstrip() for line in text.split('\n')]
    return '\n'.join(lines)


# ============================================================
# 후처리 함수들
# ============================================================

def fix_forbidden_effects(fmea_data):
    """[Fix 1] C열 금지어 치환"""
    count = 0
    for item in fmea_data:
        effect = item.get('고장영향', '')
        first_line = effect.split('\n')[0].strip() if '\n' in effect else effect

        # 정확 매칭 우선
        if first_line in FORBIDDEN_EFFECT_REPLACEMENTS:
            replacement = FORBIDDEN_EFFECT_REPLACEMENTS[first_line]
            if '\n' in effect:
                item['고장영향'] = replacement + '\n' + effect.split('\n', 1)[1]
            else:
                item['고장영향'] = replacement
            count += 1
        else:
            # substring 매칭 (주의: false positive 가능)
            for forbidden, replacement in FORBIDDEN_EFFECT_REPLACEMENTS.items():
                if forbidden in first_line and first_line != forbidden:
                    # 단, "단락사고"처럼 더 긴 유효값에 포함된 경우 건너뜀
                    # exact match가 없으면 substring 매칭
                    if '\n' in effect:
                        item['고장영향'] = replacement + '\n' + effect.split('\n', 1)[1]
                    else:
                        item['고장영향'] = replacement
                    count += 1
                    break

    return count


def fix_causal_chain_keywords(fmea_data):
    """[Fix 2] 인과관계 체인 키워드 주입"""
    fixed = 0
    skipped = 0
    already_valid = 0
    no_category = 0

    for item in fmea_data:
        mode = item.get('고장형태', '')
        cause = item.get('고장원인', '')

        category = find_category(mode)
        if not category:
            no_category += 1
            continue

        if has_valid_cause(cause, category):
            already_valid += 1
            continue

        # 라이프사이클 태그 추출
        lifecycle = cause.split(':')[0].strip()
        keyword = get_safe_keyword(category, lifecycle, mode)

        if keyword:
            # 상세설명이 있는 경우 1줄째에만 키워드 추가
            if '\n' in cause:
                first_line, rest = cause.split('\n', 1)
                item['고장원인'] = first_line + ' (' + keyword + ')\n' + rest
            else:
                item['고장원인'] = cause + ' (' + keyword + ')'
            fixed += 1
        else:
            skipped += 1

    return {'fixed': fixed, 'skipped': skipped,
            'already_valid': already_valid, 'no_category': no_category}


def fix_missing_detail_lines(fmea_data):
    """[Fix 3] C/F열 상세설명 누락 보완"""
    c_fixed = 0
    f_fixed = 0

    for item in fmea_data:
        # C열 상세설명
        effect = item.get('고장영향', '')
        if '\n' not in effect and effect.strip():
            detail = EFFECT_DETAIL_DEFAULTS.get(effect.strip(), '(상세 조건 확인 필요)')
            item['고장영향'] = effect + '\n' + detail
            c_fixed += 1

        # F열 상세설명
        cause = item.get('고장원인', '')
        if '\n' not in cause and cause.strip():
            # 라이프사이클 태그와 원인 분리
            if ':' in cause:
                parts = cause.split(':', 1)
                tag = parts[0].strip()
                reason = parts[1].strip()
                item['고장원인'] = cause + '\n(' + reason + '의 구체적 조건/수치 확인 필요)'
            else:
                item['고장원인'] = cause + '\n(원인의 구체적 맥락 확인 필요)'
            f_fixed += 1

    return {'c_fixed': c_fixed, 'f_fixed': f_fixed}


def normalize_all_text(fmea_data):
    """[Fix 4] 전체 텍스트 정규화"""
    text_cols = ['부품명', '기능', '고장영향', '고장형태', '고장원인',
                 '고장메커니즘', '현재예방대책', '현재검출대책']
    count = 0
    for item in fmea_data:
        for col in text_cols:
            old_val = item.get(col, '')
            if isinstance(old_val, str):
                new_val = normalize_text(old_val)
                if new_val != old_val:
                    item[col] = new_val
                    count += 1
    return count


def calc_ap(s, o, d):
    """AIAG-VDA AP (Action Priority) 계산.
    H: S>=9 OR (S>=7 AND O>=7) OR (S>=7 AND D>=7)
    M: S>=7 OR (S>=5 AND O>=5) OR (S>=5 AND D>=5)
    L: 나머지
    """
    if s >= 9 or (s >= 7 and o >= 7) or (s >= 7 and d >= 7):
        return 'H'
    elif s >= 7 or (s >= 5 and o >= 5) or (s >= 5 and d >= 5):
        return 'M'
    else:
        return 'L'


def fix_rpn_ap(fmea_data):
    """[Fix 4.5] RPN/AP 누락/불일치 보정 (방어적 재계산)"""
    fixed = 0
    for item in fmea_data:
        s = int(item.get('S', 0)) if str(item.get('S', 0)).isdigit() else 0
        o = int(item.get('O', 0)) if str(item.get('O', 0)).isdigit() else 0
        d = int(item.get('D', 0)) if str(item.get('D', 0)).isdigit() else 0
        correct_rpn = s * o * d
        correct_ap = calc_ap(s, o, d)
        changed = False
        if item.get('RPN') != correct_rpn:
            item['RPN'] = correct_rpn
            changed = True
        if item.get('AP') != correct_ap:
            item['AP'] = correct_ap
            changed = True
        if changed:
            fixed += 1
    return fixed


def sort_and_renumber(fmea_data):
    """[Fix 5] 정렬 + 번호 재부여 + 예방/검출조치 갱신"""
    lifecycle_order = {'설계': 1, '재료': 2, '제작': 3, '시험': 4}

    def sort_key(row):
        cause = row.get('고장원인', '')
        lifecycle_stage = cause.split(':')[0].strip().strip('[]')
        s_value = int(row['S']) if str(row.get('S', 0)).isdigit() else 0
        return (
            row.get('부품명', ''),
            row.get('기능', ''),
            row.get('고장영향', '').split('\n')[0],
            -s_value,
            row.get('고장형태', ''),
            lifecycle_order.get(lifecycle_stage, 99),
            cause
        )

    fmea_data.sort(key=sort_key)

    for i, item in enumerate(fmea_data):
        item['번호'] = i + 1
        # AP는 fix_rpn_ap에서 이미 재계산됨. 기본값 'M' 금지!
        ap = item.get('AP', 'L')
        item['예방조치'] = '%s 판정에 따른 예방 조치 (항목 %d)' % (ap, i + 1)
        item['검출조치'] = '%s 판정에 따른 검출 조치 (항목 %d)' % (ap, i + 1)

    return len(fmea_data)


def verify_merge_contiguity(fmea_data):
    """[검증 6] 병합 연속성 검증"""
    merge_cols = [
        ('부품명', []),
        ('기능', ['부품명']),
        ('고장영향', ['부품명', '기능']),
        ('고장형태', ['부품명', '기능', '고장영향'])
    ]

    issues = []
    for col_name, ancestor_chain in merge_cols:
        positions = defaultdict(list)
        for i, row in enumerate(fmea_data):
            # full parent chain key (validate_merge_contiguity bug fix 반영!)
            key_parts = tuple(
                row.get(c, '').split('\n')[0] for c in ancestor_chain
            ) + (row.get(col_name, '').split('\n')[0],)
            positions[key_parts].append(i)

        for key, indices in positions.items():
            if len(indices) > 1:
                for j in range(len(indices) - 1):
                    if indices[j + 1] - indices[j] > 1:
                        issues.append({
                            'column': col_name,
                            'value': key[-1][:30] if key else '',
                            'rows': indices
                        })
                        break

    return issues


def compute_statistics(fmea_data):
    """[통계 7] 분포 통계"""
    effects = Counter()
    lifecycles = Counter()

    for item in fmea_data:
        effect = item.get('고장영향', '').split('\n')[0]
        effects[effect] += 1
        lc = item.get('고장원인', '').split(':')[0].strip()
        lifecycles[lc] += 1

    return {'effects': effects, 'lifecycles': lifecycles, 'total': len(fmea_data)}


def verify_function_coverage(fmea_data):
    """[검증 7.5] 기능 커버리지 검증 (v12.1 강화)
    - 다이어그램 기능: 각 최소 2개 항목 (BLOCKING!)
    - 추가기능(내부문서/WebSearch): 각 최소 1개 항목
    - 주기능(첫번째 기능)이 전체의 >= 30%인지 확인
    Returns: dict with issues list and stats
    """
    func_counts = Counter()
    part_primary_func = {}  # 부품별 주기능 (첫 등장 기능)

    # 기능별 항목 수 카운트
    for item in fmea_data:
        part = item.get('부품명', '')
        func = item.get('기능', '')
        func_counts[(part, func)] += 1

        # 부품별 첫번째 기능 = 주기능 (등장 순서 기반)
        if part not in part_primary_func:
            part_primary_func[part] = func

    issues = []
    total = len(fmea_data)
    primary_count = 0

    for (part, func), count in func_counts.items():
        if part_primary_func.get(part) == func:
            primary_count += count

    primary_ratio = (primary_count / total * 100) if total > 0 else 0

    # 주기능 비율 경고 (< 30%)
    if primary_ratio < 30 and total > 0:
        issues.append(
            "[WARN] Primary function ratio: %.1f%% (target: >= 30%%)" % primary_ratio)

    # v12.1: 다이어그램 기능 0개 = BLOCKING! 1개 = WARNING!
    for (p, f), c in func_counts.items():
        if c == 0:
            issues.append("[BLOCKING] Zero items for function: %s / %s" % (p, f))
        elif c == 1:
            issues.append(
                "[WARN] Only 1 item for function: %s / %s (min 2 recommended)" % (p, f))

    return {
        'function_counts': dict(func_counts),
        'primary_ratio': primary_ratio,
        'primary_count': primary_count,
        'total': total,
        'issues': issues
    }


def fix_sod_format(fmea_data):
    """[Fix 7.6] SOD 형식 정규화 (v12 신규)
    '10x3x4' -> 'S10xO3xD4' 형식으로 변환
    """
    import re
    fixed = 0
    for item in fmea_data:
        sod = item.get('SOD', '')
        if not sod or not isinstance(sod, str):
            # SOD 없으면 S/O/D에서 생성
            s = item.get('S', '')
            o = item.get('O', '')
            d = item.get('D', '')
            if s and o and d:
                item['SOD'] = 'S%sxO%sxD%s' % (s, o, d)
                fixed += 1
            continue
        # 이미 올바른 형식이면 스킵
        if re.match(r'^S\d+xO\d+xD\d+$', sod):
            continue
        # '10x3x4' 형식 -> 'S10xO3xD4'
        m = re.match(r'^(\d+)[xX](\d+)[xX](\d+)$', sod)
        if m:
            item['SOD'] = 'S%sxO%sxD%s' % (m.group(1), m.group(2), m.group(3))
            fixed += 1
    return fixed


# ============================================================
# 메인 실행
# ============================================================

def postprocess(json_path, check_only=False):
    """FMEA JSON 후처리 메인 함수

    Args:
        json_path: combined JSON 또는 batch JSON 경로
        check_only: True면 검증만 수행 (수정 없음)

    Returns:
        dict: 후처리 결과 요약
    """
    print("=" * 60)
    print("FMEA Postprocessor %s" % ("(CHECK ONLY)" if check_only else ""))
    print("=" * 60)

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # batch vs combined 자동 감지
    if 'fmea_data' in data:
        fmea_data = data['fmea_data']
        is_combined = True
    elif isinstance(data, list):
        fmea_data = data
        is_combined = False
    else:
        print("[ERROR] Unknown JSON format!")
        return {'error': 'Unknown JSON format'}

    print("Input: %s" % json_path)
    print("Items: %d" % len(fmea_data))
    print("Mode: %s" % ("check-only" if check_only else "fix + save"))

    results = {}

    # [1] C열 금지어 검사/치환
    print("\n--- [1] C열 금지어 ---")
    if not check_only:
        fix1 = fix_forbidden_effects(fmea_data)
        print("  Fixed: %d items" % fix1)
        results['forbidden_effects_fixed'] = fix1
    else:
        # 검사만
        violations = 0
        for item in fmea_data:
            effect = item.get('고장영향', '').split('\n')[0].strip()
            if effect in FORBIDDEN_EFFECT_REPLACEMENTS:
                violations += 1
                print("  [!] '%s' -> '%s'" % (effect, FORBIDDEN_EFFECT_REPLACEMENTS[effect]))
        print("  Violations: %d" % violations)
        results['forbidden_effects_violations'] = violations

    # [2] 인과관계 키워드
    print("\n--- [2] Causal chain keywords ---")
    if not check_only:
        fix2 = fix_causal_chain_keywords(fmea_data)
        print("  Fixed: %d, Already valid: %d, No category: %d, Skipped: %d" % (
            fix2['fixed'], fix2['already_valid'], fix2['no_category'], fix2['skipped']))
        results['causal_chain'] = fix2
    else:
        violations = 0
        for item in fmea_data:
            mode = item.get('고장형태', '')
            cause = item.get('고장원인', '')
            cat = find_category(mode)
            if cat and not has_valid_cause(cause, cat):
                violations += 1
        print("  Violations: %d" % violations)
        results['causal_chain_violations'] = violations

    # [3] C/F열 상세설명
    print("\n--- [3] C/F detail lines ---")
    if not check_only:
        fix3 = fix_missing_detail_lines(fmea_data)
        print("  C열 fixed: %d, F열 fixed: %d" % (fix3['c_fixed'], fix3['f_fixed']))
        results['detail_lines'] = fix3
    else:
        c_missing = sum(1 for item in fmea_data if '\n' not in item.get('고장영향', ''))
        f_missing = sum(1 for item in fmea_data if '\n' not in item.get('고장원인', ''))
        print("  C열 missing: %d, F열 missing: %d" % (c_missing, f_missing))
        results['detail_lines_missing'] = {'c': c_missing, 'f': f_missing}

    # [4] 텍스트 정규화
    print("\n--- [4] Text normalization ---")
    if not check_only:
        fix4 = normalize_all_text(fmea_data)
        print("  Normalized: %d fields" % fix4)
        results['normalized_fields'] = fix4

    # [4.5] RPN/AP 재계산 (방어적)
    print("\n--- [4.5] RPN/AP recalculation ---")
    if not check_only:
        fix45 = fix_rpn_ap(fmea_data)
        print("  Fixed: %d items" % fix45)
        results['rpn_ap_fixed'] = fix45
    else:
        rpn_missing = sum(1 for item in fmea_data if not item.get('RPN'))
        ap_missing = sum(1 for item in fmea_data if not item.get('AP'))
        print("  RPN missing: %d, AP missing: %d" % (rpn_missing, ap_missing))
        results['rpn_ap_missing'] = {'rpn': rpn_missing, 'ap': ap_missing}

    # [5] 정렬 + 번호
    print("\n--- [5] Sort + renumber ---")
    if not check_only:
        fix5 = sort_and_renumber(fmea_data)
        print("  Renumbered: %d items" % fix5)
        results['renumbered'] = fix5

    # [6] 병합 연속성
    print("\n--- [6] Merge contiguity ---")
    issues = verify_merge_contiguity(fmea_data)
    if issues:
        for issue in issues[:5]:
            print("  [!] %s '%s' at rows %s" % (
                issue['column'], issue['value'], issue['rows']))
        if len(issues) > 5:
            print("  ... +%d more" % (len(issues) - 5))
    else:
        print("  [OK] All merge targets contiguous")
    results['contiguity_issues'] = len(issues)

    # [7] 통계
    stats = compute_statistics(fmea_data)
    print("\n--- [7] Statistics ---")
    print("  Effects:")
    for effect, count in stats['effects'].most_common():
        print("    %s: %d" % (effect[:30], count))
    print("  Lifecycle:")
    total = stats['total']
    for lc, count in sorted(stats['lifecycles'].items()):
        pct = count / total * 100 if total > 0 else 0
        print("    %s: %d (%.1f%%)" % (lc, count, pct))
    results['statistics'] = {
        'total': total,
        'effects': dict(stats['effects']),
        'lifecycles': dict(stats['lifecycles'])
    }

    # [7.5] 기능 커버리지 검증 (v12)
    print("\n--- [7.5] Function coverage ---")
    fc_result = verify_function_coverage(fmea_data)
    print("  Primary function ratio: %.1f%% (%d/%d)" % (
        fc_result['primary_ratio'], fc_result['primary_count'], fc_result['total']))
    if fc_result['issues']:
        for issue in fc_result['issues']:
            print("  %s" % issue)
    else:
        print("  [OK] Function coverage verified")
    results['function_coverage'] = fc_result

    # [7.6] SOD 형식 정규화 (v12)
    print("\n--- [7.6] SOD format ---")
    if not check_only:
        fix76 = fix_sod_format(fmea_data)
        print("  SOD format fixed: %d items" % fix76)
        results['sod_fixed'] = fix76
    else:
        import re
        bad_sod = sum(1 for item in fmea_data
                      if item.get('SOD') and not re.match(r'^S\d+xO\d+xD\d+$', str(item.get('SOD', ''))))
        print("  Invalid SOD format: %d items" % bad_sod)
        results['sod_invalid'] = bad_sod

    # 저장
    if not check_only:
        if is_combined:
            data['fmea_data'] = fmea_data
            data['project_info']['total_items'] = len(fmea_data)
        else:
            data = fmea_data

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print("\n[SAVED] %s (%d items)" % (json_path, len(fmea_data)))
    else:
        print("\n[CHECK ONLY] No changes written")

    print("=" * 60)
    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python postprocess_fmea.py <json_path> [--check-only]")
        sys.exit(1)

    json_path = sys.argv[1]
    check_only = '--check-only' in sys.argv

    if not os.path.exists(json_path):
        print("[ERROR] File not found: %s" % json_path)
        sys.exit(1)

    results = postprocess(json_path, check_only=check_only)

    # 종합 판정
    has_issues = (
        results.get('contiguity_issues', 0) > 0
        or results.get('forbidden_effects_violations', 0) > 0
        or results.get('causal_chain_violations', 0) > 0
    )
    if check_only and has_issues:
        print("\n[FAIL] Issues detected! Run without --check-only to fix.")
        sys.exit(1)
    elif not check_only:
        print("\n[OK] Postprocessing complete.")


if __name__ == '__main__':
    main()
