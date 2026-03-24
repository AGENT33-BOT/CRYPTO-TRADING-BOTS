# Trading Bot Auto-Restart Monitor
# Run this to keep bots alive

function Check-TradingBots {
    $pythonProcs = Get-Process python -ErrorAction SilentlyContinue
    $trendlineRunning = $false
    $originalRunning = $false
    $restartNeeded = $false
    
    if ($pythonProcs) {
        # Check log files to identify which bot is which
        $trendlineLog = "C:\Users\digim\clawd\crypto_trader\trendline_trading.log"
        $originalLog = "C:\Users\digim\clawd\crypto_trader\bybit_trading.log"
        
        # Check if logs have recent activity (within last 10 minutes)
        $trendlineRecent = $false
        $originalRecent = $false
        
        if (Test-Path $trendlineLog) {
            $lastWrite = (Get-Item $trendlineLog).LastWriteTime
            if ((Get-Date) - $lastWrite -lt [TimeSpan]::FromMinutes(10)) {
                $trendlineRecent = $true
            }
        }
        
        if (Test-Path $originalLog) {
            $lastWrite = (Get-Item $originalLog).LastWriteTime
            if ((Get-Date) - $lastWrite -lt [TimeSpan]::FromMinutes(10)) {
                $originalRecent = $true
            }
        }
        
        $trendlineRunning = $trendlineRecent
        $originalRunning = $originalRecent
    }
    
    return @{
        TrendlineRunning = $trendlineRunning
        OriginalRunning = $originalRunning
        PythonCount = ($pythonProcs | Measure-Object).Count
    }
}

function Restart-TradingBots {
    Write-Host "$(Get-Date) - Restarting trading bots..." -ForegroundColor Yellow
    
    # Kill any existing Python processes
    Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    
    # Start Trendline Trader
    $trendlineJob = Start-Job -ScriptBlock {
        Set-Location "C:\Users\digim\clawd\crypto_trader"
        python trendline_trader.py
    } -Name "TrendlineTrader"
    
    # Start Original Trader
    $originalJob = Start-Job -ScriptBlock {
        Set-Location "C:\Users\digim\clawd\crypto_trader"
        python bybit_trader_clean.py
    } -Name "OriginalTrader"
    
    Write-Host "$(Get-Date) - Bots restarted!" -ForegroundColor Green
    return $true
}

# Main monitoring loop
Write-Host "Starting Trading Bot Monitor..." -ForegroundColor Cyan
Write-Host "Checking every 5 minutes. Press Ctrl+C to stop." -ForegroundColor Gray

while ($true) {
    $status = Check-TradingBots
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    Write-Host "[$timestamp] Status: Trendline=$($status.TrendlineRunning), Original=$($status.OriginalRunning), PythonProcesses=$($status.PythonCount)"
    
    if (-not $status.TrendlineRunning -or -not $status.OriginalRunning) {
        Write-Host "[$timestamp] ALERT: Bot(s) not running! Restarting..." -ForegroundColor Red
        Restart-TradingBots
        
        # Send alert (you can integrate with Telegram here)
        # For now, just log it
        Add-Content -Path "C:\Users\digim\clawd\crypto_trader\bot_monitor.log" -Value "[$timestamp] Bots restarted"
    }
    
    # Wait 5 minutes
    Start-Sleep -Seconds 300
}
