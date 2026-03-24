# Auto Position Opener Monitor - Simple check
import psutil
import subprocess
import datetime
import os

timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
SCRIPT = 'auto_position_opener.py'
LOG = 'monitor_status.log'

log_lines = []
log_lines.append("="*60)
log_lines.append(f"Auto Position Opener Monitor - {timestamp}")
log_lines.append("="*60)

# Check if running
running = False
pid = None
cmd = None

for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        cmdline = proc.info.get('cmdline') or []
        cmd_str = ' '.join(cmdline)
        if SCRIPT in cmd_str and 'python' in proc.info.get('name', '').lower():
            running = True
            pid = proc.info['pid']
            cmd = cmd_str
            break
    except:
        pass

if running:
    log_lines.append(f"[OK] {SCRIPT} is RUNNING (PID: {pid})")
else:
    log_lines.append(f"[WARN] {SCRIPT} is NOT running - restarting...")
    try:
        proc = subprocess.Popen(
            ['python', SCRIPT],
            cwd=r'C:\Users\digim\clawd\crypto_trader',
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        log_lines.append(f"[OK] Restarted {SCRIPT} (PID: {proc.pid})")
    except Exception as e:
        log_lines.append(f"[ERROR] Failed to restart: {e}")

log_lines.append("="*60)

# Write to log and print
try:
    with open(LOG, 'a') as f:
        for line in log_lines:
            f.write(f"[{timestamp}] {line}\n")
            print(line)
except:
    for line in log_lines:
        print(line)
