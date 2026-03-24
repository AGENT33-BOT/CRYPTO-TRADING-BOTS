import psutil
import subprocess
import sys
from datetime import datetime

LOG_FILE = "opener_monitor.log"

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# Check if auto_position_opener is running
found = False
for p in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        cmdline = p.info.get('cmdline') or []
        cmdline_str = ' '.join(cmdline)
        if 'auto_position_opener' in cmdline_str and 'python' in p.info['name'].lower():
            log(f"Found running: PID {p.info['pid']} - {cmdline_str[:100]}")
            found = True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

if not found:
    log("auto_position_opener.py NOT RUNNING")
    log("WARNING: Bot is DISABLED per MEMORY.md - was violating trading rules")
    log("SKIPPING restart - DO NOT restart auto_position_opener.py")
else:
    log("auto_position_opener.py is running")
