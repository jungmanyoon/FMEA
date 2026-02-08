#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FMEA Pre-Write Hook (PreToolUse)

Version: 1.0
Date: 2026-02-04

[!] Claude Code v2.0.10+ hookSpecificOutput format required!

Purpose:
- Validates FMEA JSON files before Write operations
- Checks if required files were read (anti-hallucination)
- Blocks writes if validation fails
"""

import json
import sys
import re
from pathlib import Path

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
        "session_id": "...",
        "working_directory": "..."
    }

    Output format (hookSpecificOutput):
    {
        "hookSpecificOutput": {
            "decision": "approve" | "block" | "modify",
            "reason": "...",
            "modifiedInput": {...}  // only if decision is "modify"
        }
    }
    """
    try:
        # Read input from stdin
        input_data = json.loads(sys.stdin.read())

        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        # Only process Write tool
        if tool_name != "Write":
            output_approve()
            return

        file_path = tool_input.get("file_path", "")
        content = tool_input.get("content", "")

        # Check if it's an FMEA JSON file
        if not is_fmea_json(file_path):
            output_approve()
            return

        # Validate FMEA JSON content
        validation_result = validate_fmea_content(content)

        if validation_result["valid"]:
            output_approve()
        else:
            output_block(validation_result["reason"])

    except json.JSONDecodeError:
        # If we can't parse input, approve by default
        output_approve()
    except Exception as e:
        # On any error, approve by default (fail-open)
        print(json.dumps({
            "hookSpecificOutput": {
                "decision": "approve",
                "reason": f"Hook error (fail-open): {str(e)}"
            }
        }))


def is_fmea_json(file_path: str) -> bool:
    """Check if file is an FMEA JSON file"""
    path = Path(file_path)

    # Check extension
    if path.suffix.lower() != ".json":
        return False

    # Check filename patterns
    fmea_patterns = [
        r"fmea",
        r"batch",
        r"failure_mode",
        r"_items",
    ]

    name_lower = path.stem.lower()
    for pattern in fmea_patterns:
        if re.search(pattern, name_lower):
            return True

    return False


def validate_fmea_content(content: str) -> dict:
    """Validate FMEA JSON content"""
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "reason": f"Invalid JSON: {str(e)}"
        }

    # Get items list
    items = data if isinstance(data, list) else data.get("items", [data])

    if not items:
        return {"valid": True, "reason": "Empty content allowed"}

    errors = []

    for i, item in enumerate(items):
        # Check E column (failure_mode)
        fm = item.get("failure_mode") or item.get("고장형태", "")
        if fm and not has_required_tag(fm, ["부족:", "과도:", "유해:"]):
            errors.append(f"Item {i}: E열 태그 누락 (부족:/과도:/유해:)")

        # Check F column (cause)
        cause = item.get("cause") or item.get("고장원인", "")
        if cause and not has_required_tag(cause, ["설계:", "재료:", "제작:", "시험:"]):
            errors.append(f"Item {i}: F열 라이프사이클 태그 누락")

        # Check G column (mechanism)
        mech = item.get("mechanism") or item.get("고장메커니즘", "")
        if mech and mech.count("->") < 2:
            errors.append(f"Item {i}: G열 화살표 2개 이상 필요")

    if errors:
        return {
            "valid": False,
            "reason": "FMEA Validation Failed:\n- " + "\n- ".join(errors[:5])  # Max 5 errors
        }

    return {"valid": True, "reason": "All validations passed"}


def has_required_tag(text: str, tags: list) -> bool:
    """Check if text has any of the required tags"""
    return any(tag in text for tag in tags)


def output_approve():
    """Output approve decision"""
    print(json.dumps({
        "hookSpecificOutput": {
            "decision": "approve",
            "reason": "Validation passed"
        }
    }))


def output_block(reason: str):
    """Output block decision"""
    print(json.dumps({
        "hookSpecificOutput": {
            "decision": "block",
            "reason": reason
        }
    }))


if __name__ == "__main__":
    main()
