import subprocess
import time

bots = [
    ('mean_reversion_trader.py', 'Mean Reversion'),
    ('momentum_trader.py', 'Momentum'),
    ('scalping_bot.py', 'Scalping'),
]

for script, name in bots:
    print(f"Stopping {name}...")
    try:
        # Find and kill the process
        result = subprocess.run(
            ['powershell', '-Command',
             f"Get-WmiObject Win32_Process -Filter \"name='python.exe'\" | Where-Object {{ $_.CommandLine -like '*{script}*' }} | ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }}"],
            capture_output=True, text=True
        )
        print(f"  {name} stopped")
    except Exception as e:
        print(f"  Error stopping {name}: {e}")
    time.sleep(1)

print("\nAll bots stopped!")
