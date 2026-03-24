@echo off
cd C:\Users\digim\clawd\crypto_trader
python -c "import psutil; procs=[p for p in psutil.process_iter(['pid','cmdline']) if 'auto_position_opener.py' in str(p.info.get('cmdline',''))]; print('RUNNING' if procs else 'NOT RUNNING')" > temp_status.txt
set /p STATUS=<temp_status.txt
del temp_status.txt

if "%STATUS%"=="RUNNING" (
    echo [%date% %time%] ✅ Auto Position Opener is RUNNING >> opener_monitor.log
    echo ✅ Auto Position Opener is RUNNING
) else (
    echo [%date% %time%] ❌ Auto Position Opener NOT RUNNING - Restarting... >> opener_monitor.log
    echo ❌ Auto Position Opener NOT RUNNING - Restarting...
    start /B python auto_position_opener.py
    echo [%date% %time%] ✅ RESTARTED Auto Position Opener >> opener_monitor.log
    echo ✅ RESTARTED Auto Position Opener
)
