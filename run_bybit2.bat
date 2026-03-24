@echo off
echo ======================================
echo   AGENT BYBIT2 - Trading Bot Launcher
echo   Account: $100 Budget
echo ======================================
echo.

set SCRIPT_DIR=%~dp0
cd /d %SCRIPT_DIR%

if "%1"=="mean_reversion" goto mean_reversion
if "%1"=="momentum" goto momentum
if "%1"=="scalping" goto scalping
if "%1"=="all" goto all
if "%1"=="status" goto status
if "%1"=="stop" goto stop

:help
echo Usage: run_bybit2.bat [command]
echo.
echo Commands:
echo   mean_reversion  - Start mean reversion bot
echo   momentum        - Start momentum bot
echo   scalping        - Start scalping bot
echo   all             - Start all Bybit2 bots
echo   status          - Check bot status
echo   stop            - Stop all Bybit2 bots
echo.
goto end

:mean_reversion
echo Starting Bybit2 Mean Reversion Bot...
start "BYBIT2-MR" python bybit2_mean_reversion.py
goto end

:momentum
echo Starting Bybit2 Momentum Bot...
start "BYBIT2-MOM" python bybit2_momentum.py
goto end

:scalping
echo Starting Bybit2 Scalping Bot...
start "BYBIT2-SCALP" python bybit2_scalping.py
goto end

:all
echo Starting ALL Bybit2 Bots...
start "BYBIT2-MR" python bybit2_mean_reversion.py
start "BYBIT2-MOM" python bybit2_momentum.py
echo All bots started!
goto end

:status
echo Checking Bybit2 Bot Status...
powershell -Command "Get-Process python | Where-Object { $_.CommandLine -like '*bybit2_*' } | Select-Object Id, @{Name='Script';Expression={$cmd = (Get-CimInstance Win32_Process -Filter \"ProcessId=$($_.Id)\").CommandLine; if ($cmd -match '(bybit2_\w+\.py)') { $matches[1] } else { 'unknown' }}}"
goto end

:stop
echo Stopping all Bybit2 bots...
powershell -Command "Get-WmiObject Win32_Process -Filter \"name='python.exe'\" | Where-Object { $_.CommandLine -like '*bybit2_*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
echo Done.
goto end

:end
