@echo off
REM Auto Position Opener Monitor
REM Checks if auto_position_opener.py is running and restarts if needed

cd /d "C:\Users\digim\clawd\crypto_trader"

echo =========================================
echo Auto Position Opener Monitor
echo =========================================
echo.

python opener_monitor.py

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Monitor reported issues
    exit /b 1
)

echo.
echo Monitor check complete.
