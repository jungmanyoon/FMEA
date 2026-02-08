#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FMEA Post-Write Hook (PostToolUse)

Version: 1.0
Date: 2026-02-04

[!] Claude Code v2.0.10+ hookSpecificOutput format required!

Purpose:
- Validates FMEA JSON files after Write operations
- Provides detailed validation feedback
- Suggests corrections if issues found
"""

import json
import sys
import re
from pathlib import Path

# Forbidden words lists (same as MCP server)
FORBIDDEN_MECHANISMS = [
    "피로", "응력집중", "크리프", "열화진행", "열피로",
    "산화", "가수분해", "전기적트리", "부분방전", "열화",
    "마모", "침식", "부식진행", "절연열화"
]

FORBIDDEN_MEASUREMENTS = [
    "증가", "저하", "상승", "감소", "철손증가", "효율저하",
    "온도상승", "전류증가", "손실증가", "저항증가"
]

FORBIDDEN_FUTURE_RESULTS = [
    "소음", "진동", "오작동", "트립", "정전", "과열",
    "화재", "폭발", "정지", "고장"
]


def main():
    """
    Main hook handler

    Expected input format (stdin JSON):
    {
        "tool_name": "Write",
        "tool_input": {
            "file_path": "/path/to/file.json",
            "content": "..."
        },
        "tool_result": "success" | error message,
        "session_id": "...",
        "working_directory": "..."
    }

    Output format (hookSpecificOutput):
    {
        "hookSpecificOutput": {
            "feedback": "...",
            "warnings": [...],
            "suggestions": [...]
        }
    }
    """
    try:
        # Read input from stdin
        input_data = json.loads(sys.stdin.read())

        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        tool_result = input_data.get("tool_result", "")

        # Only process Write tool
        if tool_name != "Write":
            output_success()
            return

        file_path = tool_input.get("file_path", "")
        content = tool_input.get("content", "")

        # Check if it's an FMEA JSON file
        if not is_fmea_json(file_path):
            output_success()
            return

        # Validate FMEA JSON content
        validation_result = validate_fmea_content_detailed(content)

        output_feedback(validation_result)

    except json.JSONDecodeError:
        output_success()
    except Exception as e:
        print(json.dumps({
            "hookSpecificOutput": {
                "feedback": f"[WARN] Post-validation error: {str(e)}",
                "warnings": [],
                "suggestions": []
            }
        }))


def is_fmea_json(file_path: str) -> bool:
    """Check if file is an FMEA JSON file"""
    path = Path(file_path)

    if path.suffix.lower() != ".json":
        return False

    fmea_patterns = [r"fmea", r"batch", r"failure_mode", r"_items"]
    name_lower = path.stem.lower()

    return any(re.search(pattern, name_lower) for pattern in fmea_patterns)


def validate_fmea_content_detailed(content: str) -> dict:
    """Detailed FMEA JSON content validation"""
    result = {
        "total_items": 0,
        "valid_items": 0,
        "warnings": [],
        "suggestions": [],
        "errors": []
    }

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        result["errors"].append(f"JSON Parse Error: {str(e)}")
        return result

    items = data if isinstance(data, list) else data.get("items", [data])
    result["total_items"] = len(items)

    for i, item in enumerate(items):
        item_valid = True

        # E Column (failure_mode) validation
        fm = item.get("failure_mode") or item.get("고장형태", "")
        if fm:
            fm_issues = validate_failure_mode(fm)
            if fm_issues:
                item_valid = False
                for issue in fm_issues:
                    result["warnings"].append(f"Item {i} E열: {issue}")

        # F Column (cause) validation
        cause = item.get("cause") or item.get("고장원인", "")
        if cause:
            if not any(tag in cause for tag in ["설계:", "재료:", "제작:", "시험:"]):
                item_valid = False
                result["warnings"].append(f"Item {i} F열: 라이프사이클 태그 누락")
                result["suggestions"].append(f"Item {i}: 원인 앞에 '설계:/재료:/제작:/시험:' 추가")

        # G Column (mechanism) validation
        mech = item.get("mechanism") or item.get("고장메커니즘", "")
        if mech:
            arrow_count = mech.count("->")
            if arrow_count < 2:
                item_valid = False
                result["warnings"].append(f"Item {i} G열: 화살표 {arrow_count}개 (2개 이상 필요)")
                result["suggestions"].append(f"Item {i}: 메커니즘 형식 '원인 -> 과정 -> 결과'")

        # H Column (prevention) validation
        prev = item.get("prevention") or item.get("현재예방대책", "")
        if prev:
            lines = [l.strip() for l in prev.split("\n") if l.strip()]
            if len(lines) < 4:
                result["warnings"].append(f"Item {i} H열: {len(lines)}줄 (4줄 이상 권장)")

        # J Column (detection) validation
        det = item.get("detection") or item.get("현재검출대책", "")
        if det:
            lines = [l.strip() for l in det.split("\n") if l.strip()]
            if len(lines) < 4:
                result["warnings"].append(f"Item {i} J열: {len(lines)}줄 (4줄 이상 권장)")

        if item_valid:
            result["valid_items"] += 1

    return result


def validate_failure_mode(fm: str) -> list:
    """Validate E column (failure_mode) and return list of issues"""
    issues = []

    # Tag check
    if not any(tag in fm for tag in ["부족:", "과도:", "유해:"]):
        issues.append("태그 누락 (부족:/과도:/유해:)")

    # Mechanism forbidden words
    for word in FORBIDDEN_MECHANISMS:
        if word in fm:
            issues.append(f"'{word}' 메커니즘 -> G열로 이동")
            break

    # Measurement forbidden words
    for word in FORBIDDEN_MEASUREMENTS:
        if word in fm:
            issues.append(f"'{word}' 측정값 -> G열로 이동")
            break

    # Future result forbidden words
    for word in FORBIDDEN_FUTURE_RESULTS:
        if word in fm:
            issues.append(f"'{word}' 미래결과 -> C열로 이동")
            break

    return issues


def output_success():
    """Output success feedback"""
    print(json.dumps({
        "hookSpecificOutput": {
            "feedback": "[O] Non-FMEA file - validation skipped",
            "warnings": [],
            "suggestions": []
        }
    }))


def output_feedback(result: dict):
    """Output validation feedback"""
    if result.get("errors"):
        feedback = f"[X] Validation Error: {result['errors'][0]}"
    elif result["warnings"]:
        feedback = f"[!] FMEA Validation: {result['valid_items']}/{result['total_items']} items valid"
    else:
        feedback = f"[O] FMEA Validation: {result['total_items']} items all valid"

    print(json.dumps({
        "hookSpecificOutput": {
            "feedback": feedback,
            "warnings": result.get("warnings", [])[:10],  # Max 10 warnings
            "suggestions": result.get("suggestions", [])[:5]  # Max 5 suggestions
        }
    }))


if __name__ == "__main__":
    main()
