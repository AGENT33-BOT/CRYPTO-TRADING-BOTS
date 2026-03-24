# Hourly Trading Bot Status Report Script
$report = @()
$report += "Trading Bot Hourly Report"
$report += "$(Get-Date -Format 'yyyy-MM-dd HH:mm') ET"
$report += ""

# Check Python processes (bots)
$pythonProcs = Get-Process python -ErrorAction SilentlyContinue
if ($pythonProcs) {
    $procCount = $pythonProcs.Count
    $report += "[OK] Bot Status: $procCount Python process(es) running"
    foreach ($proc in $pythonProcs) {
        $uptime = (Get-Date) - $proc.StartTime
        $uptimeStr = "{0}h {1}m" -f $uptime.Hours, $uptime.Minutes
        $report += "   - PID $($proc.Id) | Uptime: $uptimeStr"
    }
} else {
    $report += "[WARN] Bot Status: No Python processes found!"
}
$report += ""

# Read trendline trading log (last 5 lines)
$report += "Trendline Trader Log:"
if (Test-Path "crypto_trader/trendline_trading.log") {
    $trendlineLines = Get-Content "crypto_trader/trendline_trading.log" -Tail 5
    foreach ($line in $trendlineLines) {
        if ($line -match '(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*-\s*(INFO|ERROR|WARNING)\s*-\s*(.+)$') {
            $time = $matches[1].Substring(11, 5)
            $msg = $matches[3]
            $report += "   [$time] $msg"
        } else {
            $report += "   $line"
        }
    }
} else {
    $report += "   Log file not found"
}
$report += ""

# Read Bybit trading log (last 5 lines)
$report += "Bybit Futures Trader Log:"
if (Test-Path "crypto_trader/bybit_trading.log") {
    $bybitLines = Get-Content "crypto_trader/bybit_trading.log" -Tail 5
    foreach ($line in $bybitLines) {
        if ($line -match '(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*-\s*(INFO|ERROR|WARNING)\s*-\s*(.+)$') {
            $time = $matches[1].Substring(11, 5)
            $msg = $matches[3]
            if ($msg -match 'Balance.*\$(\d+\.\d+)') {
                $balance = $matches[1]
                $report += "   [$time] Balance: `$$balance"
            } elseif ($msg -match "Trade.*executed|Position.*opened|Position.*closed") {
                $report += "   [$time] [TRADE] $msg"
            } else {
                $report += "   [$time] $msg"
            }
        } else {
            $report += "   $line"
        }
    }
} else {
    $report += "   Log file not found"
}
$report += ""

# Output the report
$report -join "`n"
