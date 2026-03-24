import psutil
import os
from datetime import datetime

LOG_FILE = "C:\\Users\\digim\\clawd\\crypto_trader\\opener_monitor.log"

# NOTE: auto_position_opener.py is DISABLED per MEMORY.md
# This script KILLS the bot if found (prevents unauthorized trades)

# Check if auto_position_opener.py is running
killed = False
for p in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        cmdline = p.info.get('cmdline')
        if cmdline and 'auto_position_opener' in ' '.join(cmdline):
            pid = p.info['pid']
            p.kill()
            killed = True
            print(f"auto_position_opener.py found and KILLED (PID: {pid})")
            
            with open(LOG_FILE, "a") as f:
                f.write(f"{datetime.now()} - KILLED auto_position_opener.py (PID: {pid}) - BOT DISABLED\n")
            break
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
        pass

if not killed:
    print("auto_position_opener.py is NOT running - CORRECT (bot stays disabled)")
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.now()} - NOT_RUNNING - Bot correctly disabled\n")
