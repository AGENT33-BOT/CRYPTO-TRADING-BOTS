@echo off
REM Kalshi Trading Bot Launcher
REM Usage: run_kalshi.bat [test|balance|markets|positions|scan|trade]

set KALSHI_KEY_ID=2adfb182-a79d-4666-929c-c76b6a89ab98

if "%1"=="test" (
    echo Testing Kalshi API connection...
    python kalshi_trader.py --key-id %KALSHI_KEY_ID% --action markets
    exit /b
)

if "%1"=="balance" (
    echo Checking Kalshi balance...
    python kalshi_trader.py --key-id %KALSHI_KEY_ID% --action balance
    exit /b
)

if "%1"=="markets" (
    echo Listing active markets...
    python kalshi_trader.py --key-id %KALSHI_KEY_ID% --action markets
    exit /b
)

if "%1"=="positions" (
    echo Showing open positions...
    python kalshi_trader.py --key-id %KALSHI_KEY_ID% --action positions
    exit /b
)

if "%1"=="scan" (
    echo Scanning for trading opportunities...
    python kalshi_trader.py --key-id %KALSHI_KEY_ID% --action scan
    exit /b
)

if "%1"=="trade" (
    echo Usage: run_kalshi.bat trade --ticker TICKER --side yes/no --count CONTRACTS
    echo Example: run_kalshi.bat trade --ticker BTC-250131 --side yes --count 10
    exit /b
)

REM Default: Show help
echo Kalshi Trading Bot - Agent Kalshi
echo.
echo Usage: run_kalshi.bat [command]
echo.
echo Commands:
echo   test       - Test API connection (markets)
echo   balance    - Check account balance
echo   markets    - List active markets
echo   positions  - Show open positions
echo   scan       - Scan for opportunities
echo   trade      - Show manual trade help
echo.
echo Key ID: %KALSHI_KEY_ID%
echo.
echo Note: Portfolio endpoints may require additional API permissions
