# -*- coding: utf-8 -*-
"""
Windows 인코딩 유틸리티
cp949 콘솔 환경에서 UTF-8 출력을 위한 공통 모듈

사용법:
    from encoding_utils import setup_encoding
    setup_encoding()  # 스크립트 시작 시 한 번 호출
"""

import sys
import io

_ENCODING_SETUP_DONE = False


def setup_encoding():
    """
    Windows cp949 환경에서 UTF-8 출력 설정

    중복 호출되어도 안전함 (한 번만 실행)
    """
    global _ENCODING_SETUP_DONE

    if _ENCODING_SETUP_DONE:
        return

    try:
        # stdout이 있고, buffer 속성이 있으면 UTF-8로 래핑
        if sys.stdout and hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer,
                encoding='utf-8',
                errors='replace'
            )
        if sys.stderr and hasattr(sys.stderr, 'buffer'):
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer,
                encoding='utf-8',
                errors='replace'
            )
        _ENCODING_SETUP_DONE = True
    except (AttributeError, ValueError):
        # 이미 처리됨 또는 buffer 없음
        _ENCODING_SETUP_DONE = True


# 모듈 import 시 자동 실행
setup_encoding()
