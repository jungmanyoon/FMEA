@echo off
chcp 65001 >nul 2>&1
echo.
echo ============================================
echo   FMEA 플러그인 설치
echo ============================================
echo.

if not exist ".claude\skills\fmea-analysis\mcp-server\requirements.txt" (
    echo [오류] .claude 폴더가 없습니다.
    echo        GitHub에서 다운로드한 ZIP 파일에서
    echo        .claude 폴더를 이 위치에 복사하세요.
    echo.
    pause
    exit /b 1
)

echo Python 패키지를 설치합니다...
echo.
pip install -r .claude\skills\fmea-analysis\mcp-server\requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [오류] Python 패키지 설치에 실패했습니다.
    echo        Python이 설치되어 있는지 확인하세요.
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   설치 완료!
echo ============================================
echo.
echo   사용 방법:
echo   1. 이 폴더에서 CMD를 열고 claude 입력
echo   2. 프롬프트.txt 첫 줄을 수정하고 전체 복사
echo   3. Claude Code에 붙여넣기
echo.
pause
