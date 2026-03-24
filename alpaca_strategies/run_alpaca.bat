@echo off
REM Agent Alpaca Strategy Launcher
REM Run all strategies or specific ones

cd /d "%~dp0"

echo ========================================
echo     AGENT ALPACA - Strategy Launcherecho ========================================
echo.

if "%~1"=="" (
    echo Usage: run_alpaca.bat [strategy_name^|all^|test^|status]
    echo.
    echo Examples:
    echo   run_alpaca.bat all              - Run all enabled strategies
    echo   run_alpaca.bat ema_crossover    - Run EMA Crossover strategy
    echo   run_alpaca.bat test             - Test all strategies
    echo   run_alpaca.bat status           - Show strategy status
    echo.
    python alpaca_strategy_manager.py
) else if "%~1"=="test" (
    echo Running strategy tests...
    python test_strategies.py
) else if "%~1"=="status" (
    python status_check.py
) else (
    echo Running strategy: %~1
    python alpaca_strategy_manager.py %~1
)

echo.
pause
