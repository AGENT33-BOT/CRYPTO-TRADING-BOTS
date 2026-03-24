@echo off
echo ============================================
echo STOP UNDERPERFORMING STRATEGIES
echo ============================================
echo.

echo Stopping Grid Trading...
taskkill /F /FI "WINDOWTITLE eq Grid Trading Bot" 2>nul
taskkill /F /IM "python.exe" /FI "COMMANDLINE eq *grid_trader*" 2>nul

echo Stopping Funding Arbitrage...
taskkill /F /FI "WINDOWTITLE eq Funding Arbitrage*" 2>nul
taskkill /F /IM "python.exe" /FI "COMMANDLINE eq *funding_arbitrage*" 2>nul

echo Stopping Challenge Scalping...
taskkill /F /FI "WINDOWTITLE eq Challenge*" 2>nul
taskkill /F /IM "python.exe" /FI "COMMANDLINE eq *challenge*" 2>nul

echo.
echo ============================================
echo Underperforming strategies stopped!
echo ============================================
echo.
pause
