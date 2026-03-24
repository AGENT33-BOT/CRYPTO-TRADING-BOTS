import psutil
import subprocess
import sys
import os
from datetime import datetime

# Log file
LOG_FILE = "opener_monitor.log"
SCRIPT_NAME = "auto_position_opener.py"
SCRIPT_PATH = os.path.join("crypto_trader", SCRIPT_NAME)

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def is_running():
    """Check if auto_position_opener.py is running"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline') or []
            if cmdline and any(SCRIPT_NAME in str(arg) for arg in cmdline):
                return proc.info['pid'], cmdline
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None, None

def restart():
    """Restart the auto position opener"""
    log(f"Starting {SCRIPT_NAME}...")
    try:
        # Use pythonw to run without console window on Windows
        subprocess.Popen(
            [sys.executable, SCRIPT_PATH],
            cwd=os.path.dirname(os.path.abspath(SCRIPT_PATH)) or ".",
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
        )
        log(f"Started {SCRIPT_NAME} successfully")
        return True
    except Exception as e:
        log(f"ERROR starting {SCRIPT_NAME}: {e}")
        return False

def main():
    log("="*50)
    log("Auto Position Opener Monitor Check")
    
    pid, cmdline = is_running()
    
    if pid:
        log(f"[OK] {SCRIPT_NAME} is running (PID: {pid})")
        return
    
    log(f"[WARN] {SCRIPT_NAME} is NOT running - restarting...")
    
    if restart():
        log("[OK] Restart successful")
    else:
        log("[FAIL] Restart failed")
    
    log("="*50)

if __name__ == "__main__":
    main()
