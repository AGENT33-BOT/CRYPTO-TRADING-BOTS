import subprocess
import sys

bots = [
    ('Mean Reversion', 'mean_reversion'),
    ('Momentum', 'momentum'),
    ('Scalping', 'scalping'),
    ('Grid Trader', 'grid_trader'),
    ('Funding Arbitrage', 'funding_arbitrage')
]

print("="*50)
print("BOT STATUS CHECK")
print("="*50)

for name, pattern in bots:
    result = subprocess.run(
        ['powershell', '-Command',
         f"Get-CimInstance Win32_Process -Filter \"name='python.exe'\" | Where-Object {{ \$_.CommandLine -like '*{pattern}*' }} | Select-Object -First 1 ProcessId"],
        capture_output=True, text=True
    )
    running = result.returncode == 0 and result.stdout.strip() != ''
    status = "RUNNING" if running else "STOPPED"
    pid = result.stdout.strip() if running else "N/A"
    print(f"{name:20} {status} (PID: {pid})")

print("="*50)
