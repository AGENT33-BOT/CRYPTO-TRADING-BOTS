@echo off
echo ============================================
echo 🛡️ TP/SL GUARDIAN - 5 MINUTE MONITOR
echo ============================================
echo.
echo This will run continuous TP/SL checks every 5 minutes
echo.
echo Press Ctrl+C to stop
echo.

cd /d "C:\Users\digim\clawd\crypto_trader"
python tpsl_guardian_monitor.py

pause
