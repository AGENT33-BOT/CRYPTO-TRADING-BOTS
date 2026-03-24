@echo off
echo ============================================
echo STARTING TRADING BOTS - OPTIMIZED SETUP
echo ============================================
echo.
echo ONLY running proven strategies:
echo   [1] Mean Reversion (Bollinger Bands + RSI)
echo   [2] Momentum (EMA Crossover + MACD)
echo   [3] Scalping (1-min quick moves)
echo.
echo DISABLED underperformers:
echo   - Grid Trading (unreliable uptime)
echo   - Funding Arbitrage (rarely profitable)
echo   - Challenge Mode (rate limit issues)
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
echo Active Strategies: Mean Reversion + Momentum + Scalping
echo ============================================
echo.
pause
