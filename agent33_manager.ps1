# Agent33 Autonomous Trading Bot Manager
# Runs every 5 minutes via Task Scheduler
# CRITICAL: This is the primary duty - monitor and protect all trading bots

param(
    [switch]$Silent = $false
)

$ErrorActionPreference = "Continue"
$LogFile = "C:\Users\digim\clawd\crypto_trader\logs\agent33_manager.log"
$StateFile = "C:\Users\digim\clawd\crypto_trader\agent33_state.json"
$CryptoPath = "C:\Users\digim\clawd\crypto_trader"

# Ensure log directory exists
if (!(Test-Path "$CryptoPath\logs")) {
    New-Item -ItemType Directory -Path "$CryptoPath\logs" -Force | Out-Null
}

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $LogFile -Value $logEntry
    if (!$Silent) { Write-Host $logEntry }
}

function Send-TelegramAlert {
    param([string]$Message)
    # Telegram user ID for critical alerts
    $chatId = "5804173449"
    # Note: Bot token should be in environment or .env file
    # This is a placeholder - actual bot token needs to be configured
    Write-Log "TELEGRAM ALERT: $Message" "ALERT"
}

Write-Log "=== AGENT33 AUTONOMOUS MANAGER STARTING ===" "INFO"
Write-Log "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss ET')" "INFO"

# ============================================
# CHECK 1: Bot Process Status
# ============================================
Write-Log "--- CHECKING BOT PROCESSES ---" "INFO"

try {
    $pythonProcesses = Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, @{Name="CommandLine";Expression={(Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine}}
    
    $bots = @{
        'mean_reversion_bot.py' = 'Mean Reversion Bot'
        'momentum_bot.py' = 'Momentum Bot'
        'scalping_bot.py' = 'Scalping Bot'
        'grid_trader.py' = 'Grid Trading Bot'
    }
    
    $botStatus = @{}
    $stoppedBots = @()
    
    foreach ($script in $bots.Keys) {
        $isRunning = $false
        foreach ($proc in $pythonProcesses) {
            if ($proc.CommandLine -like "*$script*") {
                $isRunning = $true
                break
            }
        }
        $botStatus[$script] = $isRunning
        $status = if ($isRunning) { "RUNNING" } else { "STOPPED" }
        $icon = if ($isRunning) { "✓" } else { "✗" }
        Write-Log "$icon $($bots[$script]): $status" $(if ($isRunning) { "SUCCESS" } else { "WARNING" })
        
        if (!$isRunning) {
            $stoppedBots += $script
        }
    }
    
    # Funding Arbitrage Bot - should NOT be running per user request
    $fundingRunning = $false
    foreach ($proc in $pythonProcesses) {
        if ($proc.CommandLine -like "*funding_arbitrage.py*") {
            $fundingRunning = $true
            break
        }
    }
    if ($fundingRunning) {
        Write-Log "⚠ FUNDING ARBITRAGE BOT IS RUNNING (should be stopped!)" "CRITICAL"
        Send-TelegramAlert "CRITICAL: Funding Arbitrage Bot is running but should be STOPPED per user request!"
    } else {
        Write-Log "✓ Funding Arbitrage Bot: STOPPED (correct)" "SUCCESS"
    }
    
} catch {
    Write-Log "Error checking bot processes: $_" "ERROR"
}

# ============================================
# CHECK 2: P&L Status
# ============================================
Write-Log "--- CHECKING P&L ---" "INFO"

try {
    Set-Location $CryptoPath
    $pnlOutput = python pnl_check.py 2>&1
    
    # Parse key info from output
    $balance = ($pnlOutput | Select-String "Balance:\s+\$(\d+\.\d+)").Matches.Groups[1].Value
    $unrealized = ($pnlOutput | Select-String "Total Unrealized P&L:\s+\$(-?\d+\.\d+)").Matches.Groups[1].Value
    $positionCount = ($pnlOutput | Select-String "Open Positions \((\d+)\)").Matches.Groups[1].Value
    
    if ($balance) { Write-Log "Balance: $ $balance USDT" "INFO" }
    if ($unrealized) { 
        $pnlLevel = if ([double]$unrealized -lt -10) { "WARNING" } elseif ([double]$unrealized -lt -5) { "WARNING" } else { "INFO" }
        Write-Log "Unrealized P&L: $ $unrealized" $pnlLevel 
    }
    if ($positionCount) { Write-Log "Open Positions: $positionCount" "INFO" }
    
    # Alert on significant losses
    if ([double]$unrealized -lt -5) {
        Write-Log "ALERT: Significant unrealized loss detected: $ $unrealized" "WARNING"
        Send-TelegramAlert "WARNING: Unrealized P&L is $ $unrealized - Monitor closely!"
    }
    
} catch {
    Write-Log "Error checking P&L: $_" "ERROR"
}

# ============================================
# CHECK 3: TP/SL Status
# ============================================
Write-Log "--- CHECKING TP/SL STATUS ---" "INFO"

try {
    Set-Location $CryptoPath
    $tpslOutput = python ensure_tp_sl.py 2>&1
    
    # Check for errors or missing TP/SL
    if ($tpslOutput -match "ERROR|Failed") {
        $errors = $tpslOutput | Select-String "ERROR|Failed" | Select-Object -First 5
        foreach ($err in $errors) {
            Write-Log "TP/SL Issue: $err" "WARNING"
        }
    } else {
        Write-Log "TP/SL check completed successfully" "SUCCESS"
    }
    
} catch {
    Write-Log "Error checking TP/SL: $_" "ERROR"
}

# ============================================
# CHECK 4: Symbol Watchlist Compliance
# ============================================
Write-Log "--- CHECKING SYMBOL COMPLIANCE ---" "INFO"

$allowedSymbols = @('BTC', 'ETH', 'SOL', 'DOGE', 'XRP', 'NEAR')
$forbiddenSymbols = @('LINK', 'ADA', 'DOT', 'AVAX', 'LTC', 'BCH')

try {
    Set-Location $CryptoPath
    # Get current positions from Python
    $positionsOutput = python -c @"
import ccxt
api_key = 'bsK06QDhsagOWwFsXQ'
api_secret = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'
exchange = ccxt.bybit({'apiKey': api_key, 'secret': api_secret, 'enableRateLimit': True, 'options': {'defaultType': 'swap'}})
positions = exchange.fetch_positions()
for p in positions:
    size = float(p.get('contracts', 0) or 0)
    if size != 0:
        print(p.get('symbol', 'Unknown'))
"@ 2>$null

    $positions = $positionsOutput -split "`n" | Where-Object { $_ -match "/USDT" }
    
    foreach ($pos in $positions) {
        $symbol = ($pos -split '/')[0]
        if ($forbiddenSymbols -contains $symbol) {
            Write-Log "⚠ VIOLATION: Position in forbidden symbol $symbol detected!" "CRITICAL"
            Send-TelegramAlert "CRITICAL: Forbidden position in $symbol detected! Consider closing immediately."
        } else {
            Write-Log "✓ $symbol position compliant" "SUCCESS"
        }
    }
    
} catch {
    Write-Log "Error checking symbol compliance: $_" "ERROR"
}

# ============================================
# UPDATE STATE FILE
# ============================================
$state = @{
    lastCheck = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
    botStatus = $botStatus
    stoppedBots = $stoppedBots
}

$state | ConvertTo-Json | Set-Content $StateFile

# ============================================
# SUMMARY
# ============================================
Write-Log "=== AGENT33 CHECK COMPLETE ===" "INFO"

if ($stoppedBots.Count -gt 0) {
    Write-Log "WARNING: $($stoppedBots.Count) bot(s) stopped: $($stoppedBots -join ', ')" "WARNING"
    Send-TelegramAlert "WARNING: Bots not running: $($stoppedBots -join ', ')"
} else {
    Write-Log "All critical bots operational" "SUCCESS"
}
