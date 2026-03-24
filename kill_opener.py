import psutil
import os
from datetime import datetime

LOG_FILE = r"C:\Users\digim\clawd\crypto_trader\opener_monitor.log"

# Check if auto_position_opener.py is running
killed = False
for p in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        cmdline = p.info.get('cmdline')
        if cmdline and 'auto_position_opener' in ' '.join(cmdline):
            pid = p.info['pid']
            p.kill()
            killed = True
            print(f"KILLED auto_position_opener.py (PID: {pid})")
            
            with open(LOG_FILE, "a") as f:
                f.write(f"{datetime.now()} - KILLED auto_position_opener.py (PID: {pid}) - BOT IS DISABLED\n")
            break
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
        pass

if not killed:
    print("auto_position_opener.py is NOT running - CORRECT (bot is disabled)")
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.now()} - NOT_RUNNING - Bot correctly disabled\n")
