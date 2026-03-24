import subprocess
import sys

bots = {
    'mean_reversion': 'mean_reversion_trader.py',
    'momentum': 'momentum_trader.py',
    'scalping': 'scalping_bot.py',
    'funding': 'funding_arbitrage.py',
    'grid': 'grid_trader.py'
}

result = subprocess.run(
    ['powershell', '-Command', "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Select-Object ProcessId, CommandLine | Format-List"],
    capture_output=True, text=True
)
print(result.stdout)
print(result.stderr)
