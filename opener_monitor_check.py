import psutil
import subprocess
import os
from datetime import datetime

log_file = r'C:\Users\digim\clawd\crypto_trader\opener_monitor.log'
script_path = r'C:\Users\digim\clawd\crypto_trader\auto_position_opener.py'
work_dir = r'C:\Users\digim\clawd\crypto_trader'

# Check if auto_position_opener.py is running
running = False
pid = None
cmdline = None

for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        cmd = proc.info.get('cmdline')
        if cmd and 'auto_position_opener.py' in str(cmd):
            running = True
            pid = proc.info['pid']
            cmdline = cmd
            break
    except:
        continue

# Log results
with open(log_file, 'a') as f:
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if running:
        f.write(f'[{timestamp}] ✅ RUNNING - auto_position_opener.py (PID: {pid})\n')
        print(f'✅ Auto Position Opener is RUNNING (PID: {pid})')
        print(f'   Command: {cmdline}')
    else:
        f.write(f'[{timestamp}] ❌ NOT RUNNING - Restarting auto_position_opener.py\n')
        print('❌ Auto Position Opener NOT RUNNING - Restarting...')
        try:
            # Start the process
            process = subprocess.Popen(
                ['python', script_path],
                cwd=work_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            f.write(f'[{timestamp}] ✅ RESTARTED - auto_position_opener.py (PID: {process.pid})\n')
            print(f'✅ RESTARTED - Auto Position Opener (PID: {process.pid})')
        except Exception as e:
            f.write(f'[{timestamp}] ❌ RESTART FAILED: {e}\n')
            print(f'❌ RESTART FAILED: {e}')
