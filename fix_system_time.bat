@echo off
echo ============================================
echo SYSTEM TIME SYNC FIX
echo ============================================
echo.
echo This will sync your Windows time with internet servers
echo to fix the Bybit API timestamp error.
echo.
pause

echo [1/3] Stopping Windows Time service...
net stop w32time

echo [2/3] Configuring time servers...
w32tm /config /manualpeerlist:"time.windows.com,0x1 time.nist.gov,0x1 pool.ntp.org,0x1" /syncfromflags:manual /reliable:yes /update

echo [3/3] Starting Windows Time service and syncing...
net start w32time
w32tm /resync /force

echo.
echo ============================================
echo Time sync complete!
echo ============================================
echo.
echo Current time:
time /t
date /t
echo.
pause
