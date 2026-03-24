import psutil
import subprocess
import datetime
import os

# Configuration
SCRIPT_NAME = "auto_position_opener.py"
WORKING_DIR = r"C:\Users\digim\clawd\crypto_trader"
LOG_FILE = os.path.join(WORKING_DIR, "opener_monitor.log")

def log_message(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {msg}"
    print(log_line)
    with open(LOG_FILE, "a") as f:
        f.write(log_line + "\n")

def is_process_running():
    """Check if auto_position_opener.py is running"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline') or []
            if SCRIPT_NAME in ' '.join(cmdline):
                return proc.info['pid'], ' '.join(cmdline)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None, None

def start_process():
    """Start the auto position opener"""
    try:
        proc = subprocess.Popen(
            ['python', SCRIPT_NAME],
            cwd=WORKING_DIR,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        return proc.pid
    except Exception as e:
        log_message(f"ERROR starting process: {e}")
        return None

def main():
    log_message("=" * 50)
    log_message("Auto Position Opener Monitor - Starting check")
    
    pid, cmdline = is_process_running()
    
    if pid:
        log_message(f"[OK] {SCRIPT_NAME} is RUNNING (PID: {pid})")
    else:
        log_message(f"[WARN] {SCRIPT_NAME} is NOT RUNNING - Restarting...")
        new_pid = start_process()
        if new_pid:
            log_message(f"[OK] Successfully restarted {SCRIPT_NAME} (New PID: {new_pid})")
        else:
            log_message(f"[FAIL] FAILED to restart {SCRIPT_NAME}")
    
    log_message("Monitor check complete")

if __name__ == "__main__":
    main()
