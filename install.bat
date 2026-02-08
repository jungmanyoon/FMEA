@echo off
chcp 65001 >nul 2>&1
echo.
echo ============================================
echo   FMEA Plugin Install
echo ============================================
echo.

REM UNC 경로 대응: 현재 경로를 드라이브로 매핑
pushd "%~dp0"

if not exist ".claude\skills\fmea-analysis\mcp-server\requirements.txt" (
    echo [ERROR] .claude folder not found.
    echo         Copy .claude folder from GitHub ZIP to this location.
    echo.
    popd
    pause
    exit /b 1
)

REM Check Python 3.10+
py -3 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3 is not installed.
    echo         Download from https://www.python.org/downloads/
    echo.
    popd
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('py -3 --version 2^>^&1') do set PYVER=%%v
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do set PYMAJOR=%%a& set PYMINOR=%%b

if %PYMINOR% LSS 10 (
    echo [ERROR] Python 3.10+ required. Current: Python %PYVER%
    echo         Download from https://www.python.org/downloads/
    echo.
    popd
    pause
    exit /b 1
)

echo Python %PYVER% OK
echo.
echo Installing packages...
echo.
py -3 -m pip install -r .claude\skills\fmea-analysis\mcp-server\requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Package install failed.
    echo.
    popd
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Install Complete!
echo ============================================
echo.
echo   How to use:
echo   1. Open CMD in this folder, type: claude
echo   2. Edit first line of prompt.txt, copy all
echo   3. Paste into Claude Code
echo.
popd
pause
