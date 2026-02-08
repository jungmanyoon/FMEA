#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
normalize_gen_keys.py - Generator JSON key normalizer

Generator Worker가 영어 키(part, B, C, E, F, G, H, J)로 출력한 경우
한글 키(부품명, 기능, 고장영향, ...)로 변환하고 combined JSON을 생성.

Usage:
  python normalize_gen_keys.py <gen_dir> <output_path> [--category CAT] [--drawing DRW]
  python normalize_gen_keys.py <gen1.json> <gen2.json> ... --output <combined.json>

Examples:
  python normalize_gen_keys.py _work/ combined.json --category 권선 --drawing "권선 자재표"
  python normalize_gen_keys.py gen1.json gen2.json --output combined.json
"""

import json
import sys
import os
import glob
import argparse

# === KEY MAPPING ===
# English column letter -> Korean standard key
KEY_MAP = {
    # English column letter -> Korean standard key
    'part': '부품명',
    'B': '기능',
    'C': '고장영향',
    'E': '고장형태',
    'F': '고장원인',
    'G': '고장메커니즘',
    'H': '현재예방대책',
    'J': '현재검출대책',
    # Korean aliases -> Korean standard key (Generator variant keys)
    '원인': '고장원인',
    '메커니즘': '고장메커니즘',
    '예방조치': '현재예방대책',
    '검출방법': '현재검출대책',
    '심각도': 'S',
    '발생도': 'O',
    '검출도': 'D',
}

# Keys to remove from items (metadata ONLY! NOT FMEA content!)
# [!!] RPN, AP = Excel 필수 컬럼 (L/M열)! 삭제 금지!
# [!!] S, O, D = Excel 필수 컬럼 (D/I/K열)! 삭제 금지!
REMOVE_KEYS = {'item_no', 'validation', 'worker', 'status',
               'validation_summary', 'statistics'}

# BLOCKING 필수 키: 없으면 exit(1) (Generator가 반드시 생성해야 하는 필드)
REQUIRED_KEYS = ['부품명', '기능', '고장영향', 'S', '고장형태', '고장원인',
                 '고장메커니즘', '현재예방대책', 'O', '현재검출대책', 'D']

# WARNING 키: 없으면 경고만 (postprocess에서 S*O*D로 재계산 가능)
RECALC_KEYS = ['RPN', 'AP']


def fix_sod_format(item):
    """Fix SOD format: '10x3x4' -> 'S10xO3xD4' (v12 규격).
    Returns True if fixed."""
    import re
    sod = item.get('SOD', '')
    if not sod or not isinstance(sod, str):
        # SOD 없으면 S/O/D에서 생성
        s = item.get('S', '')
        o = item.get('O', '')
        d = item.get('D', '')
        if s and o and d:
            item['SOD'] = 'S%sxO%sxD%s' % (s, o, d)
            return True
        return False
    # 이미 올바른 형식이면 스킵
    if re.match(r'^S\d+xO\d+xD\d+$', sod):
        return False
    # '10x3x4' 또는 '10X3X4' 형식 -> 'S10xO3xD4'
    m = re.match(r'^(\d+)[xX](\d+)[xX](\d+)$', sod)
    if m:
        item['SOD'] = 'S%sxO%sxD%s' % (m.group(1), m.group(2), m.group(3))
        return True
    return False


def fix_bracket_lifecycle(text):
    """Convert [설계] -> 설계: bracket format to colon format in H/J columns."""
    import re
    # [설계] text -> 설계: text
    new_text = re.sub(r'\[(설계|재료|제작|시험)\]\s*', r'\1: ', text)
    fixed = (new_text != text)
    return new_text, fixed


def normalize_item(item):
    """Normalize a single FMEA item's keys from English to Korean.
    Returns (new_item, brackets_fixed_count, sod_fixed)."""
    new_item = {}
    bfix = 0
    for old_key, val in item.items():
        if old_key in REMOVE_KEYS:
            continue
        new_key = KEY_MAP.get(old_key, old_key)
        # Fix bracket lifecycle format in H/J columns
        if new_key in ('현재예방대책', '현재검출대책') and isinstance(val, str):
            val, fixed = fix_bracket_lifecycle(val)
            if fixed:
                bfix += 1
        new_item[new_key] = val
    # Fix SOD format (v12): '10x3x4' -> 'S10xO3xD4'
    sod_fixed = fix_sod_format(new_item)
    return new_item, bfix, sod_fixed


def detect_key_format(item):
    """Detect whether item uses English or Korean keys."""
    eng_keys = {'part', 'B', 'C', 'E', 'F', 'G', 'H', 'J'}
    kor_keys = {'부품명', '기능', '고장영향', '고장형태', '고장원인', '고장메커니즘'}
    item_keys = set(item.keys())
    eng_count = len(item_keys & eng_keys)
    kor_count = len(item_keys & kor_keys)
    if eng_count > kor_count:
        return 'english'
    elif kor_count > 0:
        return 'korean'
    return 'unknown'


def extract_items_from_file(filepath):
    """Extract all FMEA items from a gen file, handling various structures."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = []

    # Structure 1: {"effects": [{"effect": "...", "items": [...]}]}
    if 'effects' in data:
        for eff_block in data['effects']:
            effect_name = eff_block.get('effect', '')
            s_val = eff_block.get('S', 7)
            for item in eff_block.get('items', []):
                item.setdefault('S', s_val)
                items.append(item)

    # Structure 2: {"effect": "...", "items": [...]}
    elif 'items' in data:
        effect_name = data.get('effect', '')
        s_val = data.get('S', 7)
        for item in data['items']:
            item.setdefault('S', s_val)
            items.append(item)

    # Structure 3: {"fmea_data": [...]}
    elif 'fmea_data' in data:
        items = data['fmea_data']

    # Structure 4: bare list
    elif isinstance(data, list):
        items = data

    return items


def normalize_and_merge(filepaths, category='', drawing=''):
    """Read multiple gen files, normalize keys, merge into combined format."""
    all_items = []
    stats = {
        'files_processed': 0,
        'english_keys_converted': 0,
        'korean_keys_kept': 0,
        'brackets_fixed': 0,
        'sod_fixed': 0,
        'total_items': 0,
        'missing_keys': [],
        'missing_recalc_keys': [],
    }

    for fpath in filepaths:
        if not os.path.exists(fpath):
            print("[WARN] File not found: %s" % fpath)
            continue

        items = extract_items_from_file(fpath)
        fname = os.path.basename(fpath)
        stats['files_processed'] += 1

        for item in items:
            fmt = detect_key_format(item)
            if fmt == 'english':
                item, bfix, sfix = normalize_item(item)
                stats['english_keys_converted'] += 1
                stats['brackets_fixed'] += bfix
                stats['sod_fixed'] += (1 if sfix else 0)
            elif fmt == 'korean':
                # Apply KEY_MAP even to Korean items (alias normalization)
                item, bfix, sfix = normalize_item(item)
                stats['brackets_fixed'] += bfix
                stats['sod_fixed'] += (1 if sfix else 0)
                stats['korean_keys_kept'] += 1
            else:
                item, bfix, sfix = normalize_item(item)
                stats['english_keys_converted'] += 1
                stats['brackets_fixed'] += bfix
                stats['sod_fixed'] += (1 if sfix else 0)

            # Validate required keys (BLOCKING - exit 1)
            for rk in REQUIRED_KEYS:
                if rk not in item or not item[rk]:
                    stats['missing_keys'].append(
                        "Item '%s': missing '%s'" % (
                            item.get('부품명', '?'), rk))

            # Validate recalcable keys (WARNING - postprocess can fix)
            for rk in RECALC_KEYS:
                if rk not in item or not item[rk]:
                    stats['missing_recalc_keys'].append(
                        "Item '%s': missing '%s'" % (
                            item.get('부품명', '?'), rk))

            all_items.append(item)

        print("[OK] %s: %d items (%s keys)" % (
            fname, len(items),
            'english->korean' if any(
                detect_key_format(i) == 'english'
                for i in extract_items_from_file(fpath)
            ) else 'korean'))

    # Renumber item_no
    for i, item in enumerate(all_items, 1):
        item['item_no'] = i

    stats['total_items'] = len(all_items)

    # Build combined JSON with project_info (postprocessor requirement)
    combined = {
        'project_info': {
            'category': category,
            'drawing': drawing,
            'total_items': len(all_items),
        },
        'category': category,
        'drawing': drawing,
        'total_items': len(all_items),
        'fmea_data': all_items,
    }

    return combined, stats


def main():
    parser = argparse.ArgumentParser(
        description='Normalize Generator JSON keys and merge into combined JSON')
    parser.add_argument('inputs', nargs='+',
                        help='Gen JSON files or directory containing gen*.json')
    parser.add_argument('--output', '-o', default=None,
                        help='Output combined JSON path')
    parser.add_argument('--category', default='', help='FMEA category')
    parser.add_argument('--drawing', default='', help='Drawing name')
    parser.add_argument('--check-only', action='store_true',
                        help='Check key format without writing')

    args = parser.parse_args()

    # Collect input files
    filepaths = []
    for inp in args.inputs:
        if os.path.isdir(inp):
            filepaths.extend(sorted(glob.glob(os.path.join(inp, 'gen*.json'))))
        elif os.path.isfile(inp):
            filepaths.append(inp)
        else:
            print("[WARN] Not found: %s" % inp)

    if not filepaths:
        print("[ERROR] No gen JSON files found!")
        sys.exit(1)

    print("=" * 60)
    print("FMEA Gen Key Normalizer")
    print("=" * 60)
    print("Input files: %d" % len(filepaths))
    for f in filepaths:
        print("  - %s" % os.path.basename(f))
    print()

    combined, stats = normalize_and_merge(
        filepaths, args.category, args.drawing)

    print()
    print("--- Summary ---")
    print("  Files processed: %d" % stats['files_processed'])
    print("  English->Korean converted: %d" % stats['english_keys_converted'])
    print("  Korean keys kept: %d" % stats['korean_keys_kept'])
    print("  Bracket [lifecycle] fixed: %d" % stats['brackets_fixed'])
    print("  SOD format fixed: %d" % stats['sod_fixed'])
    print("  Total items: %d" % stats['total_items'])

    if stats['missing_keys']:
        print("  [ERROR] Missing REQUIRED keys: %d" % len(stats['missing_keys']))
        for mk in stats['missing_keys'][:5]:
            print("    %s" % mk)
        if len(stats['missing_keys']) > 5:
            print("    ... and %d more" % (len(stats['missing_keys']) - 5))

    if stats['missing_recalc_keys']:
        print("  [INFO] Missing recalcable keys: %d (postprocess will fix)" %
              len(stats['missing_recalc_keys']))

    if args.check_only:
        print("\n[CHECK ONLY] No file written.")
    elif args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(combined, f, ensure_ascii=False, indent=2)
        print("\n[SAVED] %s (%d items)" % (args.output, stats['total_items']))
    else:
        # Default: write to first input dir
        out_dir = os.path.dirname(filepaths[0])
        out_path = os.path.join(out_dir, '..', 'combined_normalized.json')
        out_path = os.path.normpath(out_path)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(combined, f, ensure_ascii=False, indent=2)
        print("\n[SAVED] %s (%d items)" % (out_path, stats['total_items']))

    print("=" * 60)

    # BLOCKING: exit(1) only for REQUIRED keys, not recalcable keys
    if stats['missing_keys']:
        sys.exit(1)


if __name__ == '__main__':
    main()
