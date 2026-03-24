#!/usr/bin/env python3
"""Monitor and restart auto_position_opener.py if not running"""
import psutil
import subprocess
import sys
import os
from datetime import datetime

LOG_FILE = "opener_monitor.log"
SCRIPT_PATH = r"C:\Users\digim\clawd\crypto_trader\auto_position_opener.py"

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
            cmdline = proc.info['cmdline']
            if cmdline:
                for arg in cmdline:
                    if 'auto_position_opener.py' in str(arg):
                        return proc.info['pid'], cmdline
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None, None

def restart():
    """Restart the auto position opener"""
    log("Starting auto_position_opener.py...")
    try:
        # Change to crypto_trader directory
        workdir = r"C:\Users\digim\clawd\crypto_trader"
        
        # Start detached process
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        
        proc = subprocess.Popen(
            [sys.executable, SCRIPT_PATH],
            cwd=workdir,
            creationflags=creationflags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL
        )
        log(f"Started with PID {proc.pid}")
        return True
    except Exception as e:
        log(f"Failed to start: {e}")
        return False

def main():
    log("=" * 50)
    log("Auto Position Opener Monitor - Check starting")
    
    pid, cmdline = is_running()
    
    if pid:
        log(f"[OK] auto_position_opener.py is RUNNING (PID {pid})")
        return
    
    log("[WARN] auto_position_opener.py is NOT running")
    
    if restart():
        log("[OK] Restart successful")
    else:
        log("[FAIL] Restart failed")
    
    log("=" * 50)

if __name__ == "__main__":
    main()
