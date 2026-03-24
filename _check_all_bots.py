import subprocess
import sys

bots = [
    ('mean_reversion', 'Mean Reversion'),
    ('momentum', 'Momentum'),
    ('scalping', 'Scalping'),
    ('grid_trader', 'Grid Trader'),
    ('funding_arbitrage', 'Funding Arbitrage')
]

all_running = True
running_count = 0

for bot_file, bot_name in bots:
    result = subprocess.run(
        ['powershell', '-Command',
         f'Get-CimInstance Win32_Process -Filter "name=\'python.exe\'" | Where-Object {{ $_.CommandLine -like "*{bot_file}*" }} | Select-Object -First 1 ProcessId'],
        capture_output=True, text=True
    )
    output = result.stdout.strip()
    is_running = output and output != '' and 'ProcessId' not in output or (output and len(output) < 10 and output.isdigit())
    
    if 'ProcessId' in output:
        lines = output.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and line.isdigit():
                is_running = True
                output = line
                break
    
    status = '[OK] RUNNING' if is_running else '[X] STOPPED'
    print(f"{bot_name}: {status}")
    if is_running:
        running_count += 1
        if output and output.isdigit():
            print(f"  PID: {output}")
    else:
        all_running = False

print(f"\n{'='*50}")
print(f"Total: {running_count}/{len(bots)} bots running")
if all_running:
    print("[OK] ALL SYSTEMS NOMINAL")
else:
    print("[ALERT] SOME BOTS ARE DOWN!")
    sys.exit(1)
