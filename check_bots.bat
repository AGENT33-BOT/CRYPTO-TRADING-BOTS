@echo off
echo 🤖 BOT STATUS CHECK
echo ========================================

wmic process where "commandline like '%%mean_reversion_bot%%'" get processid 2>nul | findstr [0-9] >nul
if %errorlevel% == 0 (
    for /f "tokens=*" %%a in ('wmic process where "commandline like '%%mean_reversion_bot%%'" get processid 2^>nul ^| findstr [0-9]') do (
        echo Mean Reversion: RUNNING (PID: %%a)
        goto :next1
    )
) else (
    echo Mean Reversion: STOPPED
)
:next1

wmic process where "commandline like '%%momentum_bot%%'" get processid 2>nul | findstr [0-9] >nul
if %errorlevel% == 0 (
    for /f "tokens=*" %%a in ('wmic process where "commandline like '%%momentum_bot%%'" get processid 2^>nul ^| findstr [0-9]') do (
        echo Momentum: RUNNING (PID: %%a)
        goto :next2
    )
) else (
    echo Momentum: STOPPED
)
:next2

wmic process where "commandline like '%%scalping_bot%%'" get processid 2>nul | findstr [0-9] >nul
if %errorlevel% == 0 (
    for /f "tokens=*" %%a in ('wmic process where "commandline like '%%scalping_bot%%'" get processid 2^>nul ^| findstr [0-9]') do (
        echo Scalping: RUNNING (PID: %%a)
        goto :next3
    )
) else (
    echo Scalping: STOPPED
)
:next3

wmic process where "commandline like '%%grid_trading_bot%%'" get processid 2>nul | findstr [0-9] >nul
if %errorlevel% == 0 (
    for /f "tokens=*" %%a in ('wmic process where "commandline like '%%grid_trading_bot%%'" get processid 2^>nul ^| findstr [0-9]') do (
        echo Grid Trading: RUNNING (PID: %%a)
        goto :next4
    )
) else (
    echo Grid Trading: STOPPED
)
:next4

wmic process where "commandline like '%%funding_arbitrage%%'" get processid 2>nul | findstr [0-9] >nul
if %errorlevel% == 0 (
    for /f "tokens=*" %%a in ('wmic process where "commandline like '%%funding_arbitrage%%'" get processid 2^>nul ^| findstr [0-9]') do (
        echo Funding Arbitrage: RUNNING (PID: %%a)
        goto :done
    )
) else (
    echo Funding Arbitrage: STOPPED
)
:done

echo ========================================
