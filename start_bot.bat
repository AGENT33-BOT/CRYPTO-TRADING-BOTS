@echo off
echo ========================================
echo   Trading Bot Launcher
echo ========================================
echo.
echo Select a bot to run:
echo.
echo 1. Conservative Bot (Recommended for $60 account)
echo    - Max 2 positions, 2x leverage, $5 risk per trade
echo.
echo 2. Grid Trading Bot (DOGE/USDT)
echo    - Passive income in sideways markets
echo.
echo 3. Auto Position Opener (Aggressive)
echo    - More signals, higher frequency
echo.
echo 4. Run Backtest First
echo    - Test strategies before trading
echo.
echo 5. Check Account Status
echo.
echo ========================================
echo.

set /p choice="Enter choice (1-5): "

cd /d "C:\Users\digim\clawd\crypto_trader"

if "%choice%"=="1" (
    echo Starting Conservative Bot...
    python conservative_bot.py
) else if "%choice%"=="2" (
    echo Starting Grid Trading Bot...
    python grid_trader.py
) else if "%choice%"=="3" (
    echo Starting Auto Position Opener...
    python auto_position_opener_v2.py
) else if "%choice%"=="4" (
    echo Running Backtest...
    echo.
    echo Example commands:
    echo   python backtest_strategies.py BTC/USDT:USDT compare
    echo   python backtest_strategies.py SOL/USDT:USDT trend_following
    echo   python backtest_strategies.py ETH/USDT:USDT mean_reversion
    echo.
    set /p symbol="Enter symbol (e.g., BTC/USDT:USDT): "
    set /p strategy="Enter strategy (trend_following/mean_reversion/breakout/compare): "
    python backtest_strategies.py %symbol% %strategy%
) else if "%choice%"=="5" (
    python check_balance.py
    python check_positions.py 2>nul || echo No positions script found
) else (
    echo Invalid choice
)

pause
