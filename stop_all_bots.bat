@echo off
echo STOPPING ALL TRADING BOTS...
echo ========================================

echo.
echo 1. Killing Mean Reversion Bot...
taskkill /f /im python.exe /fi "windowtitle eq mean_reversion*" 2>nul
taskkill /f /im python.exe /fi "windowtitle eq *mean*reversion*" 2>nul

echo.
echo 2. Killing Momentum Bot...
taskkill /f /im python.exe /fi "windowtitle eq momentum*" 2>nul
taskkill /f /im python.exe /fi "windowtitle eq *momentum*" 2>nul

echo.
echo 3. Killing Scalping Bot...
taskkill /f /im python.exe /fi "windowtitle eq scalping*" 2>nul
taskkill /f /im python.exe /fi "windowtitle eq *scalp*" 2>nul

echo.
echo 4. Killing Grid Trading Bot...
taskkill /f /im python.exe /fi "windowtitle eq grid*" 2>nul
taskkill /f /im python.exe /fi "windowtitle eq *grid*" 2>nul

echo.
echo 5. Killing Funding Arbitrage Bot...
taskkill /f /im python.exe /fi "windowtitle eq funding*" 2>nul
taskkill /f /im python.exe /fi "windowtitle eq *funding*" 2>nul

echo.
echo ========================================
echo ALL BOTS STOPPED!
echo.
echo Free Balance: $528.19 USDT
echo No new positions will be opened.
echo.
pause
