# -*- coding: utf-8 -*-
"""
다이아몬드 구조 검증 스크립트
FMEA의 1:N:M:K 구조 검증

다이아몬드 구조 요구사항:
- 1개 기능 -> N개 고장영향 (>=1.5 평균)
- 1개 영향 -> N개 고장형태 (>=1.5 평균)
- 1개 형태 -> N개 고장원인 (>=2.0 평균, 필수!)
- 1:1:1:1 직선 구조 비율 < 30%
"""

import sys
import io
import pandas as pd
from collections import defaultdict

# Windows cp949 인코딩 문제 해결
if sys.stdout:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def validate_diamond_structure(file_path):
    """다이아몬드 구조 검증"""

    # 엑셀 파일 읽기
    df = pd.read_excel(file_path, sheet_name='FMEA', header=None)

    # 헤더 행 찾기
    header_row = None
    cols = {}

    for i in range(min(15, len(df))):
        row = df.iloc[i]
        for j, val in enumerate(row):
            val_str = str(val).strip()
            if val_str == '기능':
                cols['기능'] = j
            elif val_str == '고장영향':
                cols['고장영향'] = j
            elif val_str == '고장형태':
                cols['고장형태'] = j
            elif val_str == '고장원인':
                cols['고장원인'] = j

        if len(cols) >= 4:
            header_row = i
            break

    print('Header row:', header_row)
    print('Column positions:', cols)
    print('Total rows:', len(df))
    print()

    # 데이터 추출 (헤더 이후)
    data = df.iloc[header_row+1:].copy()
    data.columns = range(len(data.columns))

    # 병합 셀 처리: forward fill (재발방지대책 260111)
    # Excel 병합 셀은 첫 행만 값이 있고 나머지는 NaN
    # A-E 컬럼 (부품명, 기능, 고장영향, S, 고장형태)은 병합되므로 ffill 적용
    for col_name in ['기능', '고장영향', '고장형태']:
        if col_name in cols:
            data[cols[col_name]] = data[cols[col_name]].ffill()

    # 유효한 데이터만 추출
    records = []
    for i in range(len(data)):
        row = data.iloc[i]
        func = str(row[cols['기능']]).strip() if pd.notna(row[cols['기능']]) else ''
        effect = str(row[cols['고장영향']]).strip() if pd.notna(row[cols['고장영향']]) else ''
        mode = str(row[cols['고장형태']]).strip() if pd.notna(row[cols['고장형태']]) else ''
        cause = str(row[cols['고장원인']]).strip() if pd.notna(row[cols['고장원인']]) else ''

        # nan 제외
        if func == 'nan': func = ''
        if effect == 'nan': effect = ''
        if mode == 'nan': mode = ''
        if cause == 'nan': cause = ''

        # 빈 값이 아닌 행만 포함
        if func or effect or mode or cause:
            records.append({
                'row': header_row + 2 + i,
                '기능': func,
                '고장영향': effect,
                '고장형태': mode,
                '고장원인': cause
            })

    print('Valid data rows:', len(records))
    print()

    # 다이아몬드 구조 분석
    # 1. 기능 -> 고장영향 (1:N)
    func_to_effects = defaultdict(set)
    for r in records:
        if r['기능'] and r['고장영향']:
            func_to_effects[r['기능']].add(r['고장영향'])

    # 2. 고장영향 -> 고장형태 (1:N)
    effect_to_modes = defaultdict(set)
    for r in records:
        if r['고장영향'] and r['고장형태']:
            effect_to_modes[r['고장영향']].add(r['고장형태'])

    # 3. 고장형태 -> 고장원인 (1:N) - 가장 중요!
    mode_to_causes = defaultdict(set)
    for r in records:
        if r['고장형태'] and r['고장원인']:
            mode_to_causes[r['고장형태']].add(r['고장원인'])

    print('=' * 70)
    print('[Diamond Structure Analysis]')
    print('=' * 70)

    # 1. 기능당 고장영향 개수
    print()
    print('[1] Function -> Failure Effect (1:N)')
    print('-' * 50)
    effects_per_func = [len(v) for v in func_to_effects.values()]
    avg_effects = sum(effects_per_func) / len(effects_per_func) if effects_per_func else 0
    print('  Total functions:', len(func_to_effects))
    print('  Avg effects/function: %.2f (target: >=1.5)' % avg_effects)
    print('  Min:', min(effects_per_func) if effects_per_func else 0, ', Max:', max(effects_per_func) if effects_per_func else 0)
    one_to_one_func = sum(1 for c in effects_per_func if c == 1)
    print('  1:1 count:', one_to_one_func, '(%.1f%%)' % (one_to_one_func/len(effects_per_func)*100 if effects_per_func else 0))
    print()
    print('  Details:')
    for func, effects in sorted(func_to_effects.items()):
        status = '[FAIL]' if len(effects) == 1 else '[PASS]'
        print('    %s %s: %d effects' % (status, func, len(effects)))

    # 2. 영향당 고장형태 개수
    print()
    print('[2] Failure Effect -> Failure Mode (1:N)')
    print('-' * 50)
    modes_per_effect = [len(v) for v in effect_to_modes.values()]
    avg_modes = sum(modes_per_effect) / len(modes_per_effect) if modes_per_effect else 0
    print('  Total effects:', len(effect_to_modes))
    print('  Avg modes/effect: %.2f (target: >=1.5)' % avg_modes)
    print('  Min:', min(modes_per_effect) if modes_per_effect else 0, ', Max:', max(modes_per_effect) if modes_per_effect else 0)
    one_to_one_effect = sum(1 for c in modes_per_effect if c == 1)
    print('  1:1 count:', one_to_one_effect, '(%.1f%%)' % (one_to_one_effect/len(modes_per_effect)*100 if modes_per_effect else 0))
    print()
    print('  Details:')
    for effect, modes in sorted(effect_to_modes.items()):
        status = '[FAIL]' if len(modes) == 1 else '[PASS]'
        print('    %s %s: %d modes' % (status, effect, len(modes)))

    # 3. 형태당 고장원인 개수 (가장 중요!)
    print()
    print('[3] Failure Mode -> Failure Cause (1:N) ** MOST IMPORTANT! **')
    print('-' * 50)
    causes_per_mode = [len(v) for v in mode_to_causes.values()]
    avg_causes = sum(causes_per_mode) / len(causes_per_mode) if causes_per_mode else 0
    print('  Total modes:', len(mode_to_causes))
    print('  Avg causes/mode: %.2f (target: >=2.0 REQUIRED!)' % avg_causes)
    print('  Min:', min(causes_per_mode) if causes_per_mode else 0, ', Max:', max(causes_per_mode) if causes_per_mode else 0)
    one_to_one_mode = sum(1 for c in causes_per_mode if c == 1)
    print('  1:1 count:', one_to_one_mode, '(%.1f%%)' % (one_to_one_mode/len(causes_per_mode)*100 if causes_per_mode else 0))
    print()
    print('  Details:')
    for mode, causes in sorted(mode_to_causes.items()):
        status = '[FAIL]' if len(causes) < 2 else '[PASS]'
        print('    %s %s: %d causes' % (status, mode, len(causes)))
        for cause in sorted(causes):
            print('        - %s' % cause)

    # 4. 1:1:1:1 직선 구조 비율
    print()
    print('[4] Linear Structure Ratio (1:1:1:1)')
    print('-' * 50)
    linear_count = 0
    for r in records:
        func, effect, mode, cause = r['기능'], r['고장영향'], r['고장형태'], r['고장원인']
        if not all([func, effect, mode, cause]):
            continue

        # 이 조합이 직선 구조인지 확인
        if (len(func_to_effects.get(func, set())) == 1 and
            len(effect_to_modes.get(effect, set())) == 1 and
            len(mode_to_causes.get(mode, set())) == 1):
            linear_count += 1

    total_complete = sum(1 for r in records if all([r['기능'], r['고장영향'], r['고장형태'], r['고장원인']]))
    linear_ratio = linear_count / total_complete * 100 if total_complete > 0 else 0
    print('  Complete rows:', total_complete)
    print('  Linear (1:1:1:1) rows:', linear_count)
    print('  Linear ratio: %.1f%% (target: <30%%)' % linear_ratio)

    # 최종 판정
    print()
    print('=' * 70)
    print('[FINAL VERDICT]')
    print('=' * 70)
    print()

    passed = True
    results = []

    # 기능->영향 검사
    if avg_effects >= 1.5:
        results.append(('Function->Effect', avg_effects, 1.5, 'PASS'))
    else:
        results.append(('Function->Effect', avg_effects, 1.5, 'FAIL'))
        passed = False

    # 영향->형태 검사
    if avg_modes >= 1.5:
        results.append(('Effect->Mode', avg_modes, 1.5, 'PASS'))
    else:
        results.append(('Effect->Mode', avg_modes, 1.5, 'FAIL'))
        passed = False

    # 형태->원인 검사 (가장 중요)
    if avg_causes >= 2.0:
        results.append(('Mode->Cause', avg_causes, 2.0, 'PASS'))
    else:
        results.append(('Mode->Cause', avg_causes, 2.0, 'FAIL'))
        passed = False

    # 직선 구조 비율 검사
    if linear_ratio < 30:
        results.append(('Linear Ratio', linear_ratio, 30, 'PASS'))
    else:
        results.append(('Linear Ratio', linear_ratio, 30, 'FAIL'))
        passed = False

    for name, actual, target, status in results:
        icon = '[PASS]' if status == 'PASS' else '[FAIL]'
        if 'Ratio' in name:
            print('%s %s: %.1f%% (target: <%.0f%%)' % (icon, name, actual, target))
        else:
            print('%s %s: %.2f (target: >=%.1f)' % (icon, name, actual, target))

    print()
    if passed:
        print('*** Diamond Structure Validation PASSED! ***')
    else:
        print('*** Diamond Structure Validation FAILED - Improvement Required ***')
        print()
        print('[Recommendations]')
        if avg_causes < 2.0:
            print('  ** URGENT: Add at least 2 causes per failure mode:')
            print('     - Design perspective cause')
            print('     - Manufacturing perspective cause')
            print('     - Operation/Maintenance perspective cause')
        if linear_ratio >= 30:
            print('  - Too many 1:1:1:1 linear structures. Need diverse cause/effect analysis.')
        if avg_effects < 1.5:
            print('  - Need more failure effects per function.')
        if avg_modes < 1.5:
            print('  - Need more failure modes per effect.')

    return passed


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python validate_diamond_structure.py <excel_file>')
        sys.exit(1)

    file_path = sys.argv[1]
    passed = validate_diamond_structure(file_path)
    sys.exit(0 if passed else 1)
