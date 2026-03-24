@echo off
echo ========================================
echo STARTING BOTS (NO FUNDING ARBITRAGE)
echo ========================================
echo.

cd /d C:\Users\digim\clawd\crypto_trader

echo Starting Mean Reversion Bot...
start /b python mean_reversion_trader.py > mean_reversion_restart.log 2>&1
timeout /t 2 /nobreak > nul

echo Starting Momentum Bot...
start /b python momentum_trader.py > momentum_restart.log 2>&1
timeout /t 2 /nobreak > nul

echo Starting Scalping Bot...
start /b python scalping_bot.py > scalping_restart.log 2>&1
timeout /t 2 /nobreak > nul

echo Starting Grid Trading Bot...
start /b python grid_trader.py > grid_trader_restart.log 2>&1
timeout /t 2 /nobreak > nul

echo.
echo ========================================
echo BOTS STARTED (FUNDING ARBITRAGE EXCLUDED)
echo ========================================
echo.
echo Running bots:
echo   - Mean Reversion (FUTURES ONLY)
echo   - Momentum (FUTURES ONLY)
echo   - Scalping (FUTURES ONLY)
echo   - Grid Trading (FUTURES ONLY)
echo.
echo STOPPED:
echo   - Funding Arbitrage (was buying SPOT)
echo.
pause
