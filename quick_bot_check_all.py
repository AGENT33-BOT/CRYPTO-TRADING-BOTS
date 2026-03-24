import subprocess

bots = [
    ('mean_reversion_bot', 'Mean Reversion'),
    ('momentum_bot', 'Momentum'),
    ('scalping_bot', 'Scalping'),
    ('grid_trader', 'Grid Trading'),
    ('funding_arbitrage', 'Funding Arbitrage')
]

print("="*50)
print("BOT STATUS CHECK")
print("="*50)

for script, name in bots:
    result = subprocess.run(
        ['powershell', '-Command',
         f'Get-CimInstance Win32_Process -Filter "name=\'python.exe\'" | Where-Object {{ $_.CommandLine -like "*{script}*" }} | Select-Object -First 1 ProcessId'],
        capture_output=True, text=True
    )
    output = result.stdout.strip()
    lines = [l for l in output.split('\n') if l.strip() and not l.startswith('ProcessId') and l.strip() != '---------']
    pid = lines[0].strip() if lines else ''
    status = f'RUNNING (PID: {pid})' if pid and pid.isdigit() else 'STOPPED'
    print(f'{name}: {status}')
