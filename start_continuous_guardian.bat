@echo off
echo ============================================
echo TP/SL GUARDIAN - CONTINUOUS MODE
echo ============================================
echo.
echo Running guardian every 10 seconds...
echo Press Ctrl+C to stop
echo.
:loop
python ensure_tp_sl.py >nul 2>&1
timeout /t 10 /nobreak >nul
goto loop
