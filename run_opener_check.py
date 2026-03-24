import psutil
import subprocess
import datetime
import os

log_file = 'opener_monitor.log'
script_name = 'auto_position_opener.py'

# Check if process is running
running = False
pid = None
for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        cmdline = proc.info.get('cmdline') or []
        if any(script_name in str(arg) for arg in cmdline):
            running = True
            pid = proc.info['pid']
            break
    except:
        pass

timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

if running:
    log_entry = f'[{timestamp}] [OK] {script_name} is RUNNING (PID: {pid})\n'
    status = 'RUNNING'
    action = 'No action needed'
else:
    log_entry = f'[{timestamp}] [DOWN] {script_name} NOT RUNNING - RESTARTING...\n'
    # Restart the bot
    try:
        subprocess.Popen(['python', script_name], 
                        cwd=r'C:\Users\digim\clawd\crypto_trader',
                        creationflags=subprocess.CREATE_NEW_CONSOLE)
        log_entry += f'[{timestamp}] -> Restart initiated for {script_name}\n'
        status = 'RESTARTED'
        action = 'Restart initiated'
    except Exception as e:
        log_entry += f'[{timestamp}] → ERROR restarting: {e}\n'
        status = 'ERROR'
        action = f'Error: {e}'

# Write to log
with open(log_file, 'a') as f:
    f.write(log_entry)

print(f'STATUS: {status}')
print(f'PID: {pid if pid else "N/A"}')
print(f'Action: {action}')
print(f'Log: {log_file}')
