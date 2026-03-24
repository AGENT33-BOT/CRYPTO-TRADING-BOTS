@echo off
echo ============================================
echo ⚡ CIRCUIT BREAKER - Risk Management
echo ============================================
echo.
echo This will monitor your account and stop
echo trading if losses exceed safe limits.
echo.
echo Limits:
echo   - Max Daily Loss: $10
echo   - Max Position Loss: $5
echo   - Min Free Balance: $50
echo.
echo Press Ctrl+C to stop
echo.
pause

cd /d "C:\Users\digim\clawd\crypto_trader"
python circuit_breaker.py
