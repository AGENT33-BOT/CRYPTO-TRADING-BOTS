<#
.SYNOPSIS
    Trailing Stop Agent Manager for Bybit Futures
.DESCRIPTION
    Manages the auto trailing stop agent that monitors positions and trails stops automatically.
#>

param(
    [Parameter()]
    [ValidateSet("start", "stop", "restart", "status")]
    [string]$Action = "status"
)

$AgentName = "trailing_stop_agent"
$LogFile = "trailing_stop_agent.log"

function Get-AgentStatus {
    $process = Get-Process | Where-Object { $_.ProcessName -like "*python*" -and $_.CommandLine -like "*trailing_stop_agent.py*" } | Select-Object -First 1
    
    if ($process) {
        Write-Host "🟢 Trailing Stop Agent: RUNNING (PID: $($process.Id))" -ForegroundColor Green
        
        # Show recent log entries
        if (Test-Path $LogFile) {
            Write-Host "\n📋 Recent Activity:" -ForegroundColor Cyan
            Get-Content $LogFile -Tail 10 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
        }
    } else {
        Write-Host "🔴 Trailing Stop Agent: STOPPED" -ForegroundColor Red
    }
}

function Start-Agent {
    $existing = Get-Process | Where-Object { $_.ProcessName -like "*python*" -and $_.CommandLine -like "*trailing_stop_agent.py*" } | Select-Object -First 1
    
    if ($existing) {
        Write-Host "⚠️ Agent already running (PID: $($existing.Id))" -ForegroundColor Yellow
        return
    }
    
    Write-Host "🚀 Starting Trailing Stop Agent..." -ForegroundColor Green
    
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
    }
    
    if (-not $pythonCmd) {
        Write-Host "❌ Python not found!" -ForegroundColor Red
        return
    }
    
    # Start in background
    Start-Process -FilePath $pythonCmd.Source -ArgumentList "trailing_stop_agent.py" -WindowStyle Hidden
    
    Start-Sleep -Seconds 2
    
    $newProcess = Get-Process | Where-Object { $_.ProcessName -like "*python*" -and $_.CommandLine -like "*trailing_stop_agent.py*" } | Select-Object -First 1
    
    if ($newProcess) {
        Write-Host "✅ Agent started (PID: $($newProcess.Id))" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to start agent" -ForegroundColor Red
    }
}

function Stop-Agent {
    $processes = Get-Process | Where-Object { $_.ProcessName -like "*python*" -and $_.CommandLine -like "*trailing_stop_agent.py*" }
    
    if (-not $processes) {
        Write-Host "⚠️ Agent not running" -ForegroundColor Yellow
        return
    }
    
    Write-Host "🛑 Stopping Trailing Stop Agent..." -ForegroundColor Yellow
    
    foreach ($proc in $processes) {
        Stop-Process -Id $proc.Id -Force
        Write-Host "  Stopped PID: $($proc.Id)" -ForegroundColor Gray
    }
    
    Write-Host "✅ Agent stopped" -ForegroundColor Green
}

# Main execution
Push-Location $PSScriptRoot

try {
    switch ($Action) {
        "start" { Start-Agent }
        "stop" { Stop-Agent }
        "restart" { Stop-Agent; Start-Sleep -Seconds 1; Start-Agent }
        "status" { Get-AgentStatus }
    }
} finally {
    Pop-Location
}
