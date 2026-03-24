@echo off
echo ============================================
echo STARTING TRADING BOTS - OPTIMIZED
echo ============================================
echo.
echo ACTIVE STRATEGIES (Proven Performers):
echo   [1] Mean Reversion - Bollinger Bands + RSI
echo   [2] Momentum - EMA Crossover + MACD  
echo   [3] Scalping - 1-minute quick moves
echo.
echo DISABLED (Underperforming):
echo   - Grid Trading (file issues, unreliable)
echo   - Funding Arbitrage (rarely active)
echo   - Challenge Mode (rate limit problems)
echo.
timeout /t 3 /nobreak >nul

cd /d "C:\Users\digim\clawd\crypto_trader"

echo [1/3] Starting Mean Reversion Bot...
start "Mean Reversion Bot" python mean_reversion_trader.py

echo [2/3] Starting Momentum Bot...
start "Momentum Bot" python momentum_trader.py

echo [3/3] Starting Scalping Bot...
start "Scalping Bot" python scalping_bot.py

echo.
echo ============================================
echo Running 3 proven strategies on 4 pairs:
echo ETH, NEAR, LINK, DOGE
echo ============================================
echo.
pause
