"""
Auto Position Opener Monitor
Checks if auto_position_opener.py is running and restarts if needed
"""
import psutil
import subprocess
import sys
import time
from datetime import datetime
import os

def log(message):
    """Log to console with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def is_bot_running():
    """Check if auto_position_opener.py is currently running"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline', [])
            if cmdline:
                cmd_str = ' '.join(cmdline)
                if 'auto_position_opener.py' in cmd_str:
                    return True, proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False, None

def restart_bot():
    """Restart the auto position opener bot"""
    try:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        bot_path = os.path.join(script_dir, 'auto_position_opener.py')
        
        log(f"Starting bot: {bot_path}")
        
        # Start the bot in a new subprocess
        if sys.platform == 'win32':
            # Windows
            process = subprocess.Popen(
                [sys.executable, bot_path],
                cwd=script_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            # Linux/Mac
            process = subprocess.Popen(
                [sys.executable, bot_path],
                cwd=script_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
        
        log(f"Bot restarted with PID: {process.pid}")
        return True, process.pid
        
    except Exception as e:
        log(f"[ERROR] Failed to restart bot: {e}")
        return False, None

def kill_existing_bot(pid):
    """Kill existing bot process if it's stuck"""
    try:
        process = psutil.Process(pid)
        process.terminate()
        time.sleep(2)
        if process.is_running():
            process.kill()
        log(f"Killed existing bot (PID: {pid})")
    except psutil.NoSuchProcess:
        pass
    except Exception as e:
        log(f"[ERROR] Error killing process: {e}")

def main():
    """Main monitor function"""
    log("="*60)
    log("AUTO POSITION OPENER MONITOR STARTED")
    log("="*60)
    
    running, pid = is_bot_running()
    
    if running:
        log(f"[OK] Auto Position Opener is RUNNING (PID: {pid})")
        return 0
    else:
        log("[WARN] Auto Position Opener is NOT RUNNING!")
        log("[INFO] Attempting to restart...")
        
        # Kill any zombie processes
        if pid:
            kill_existing_bot(pid)
        
        success, new_pid = restart_bot()
        
        if success:
            log(f"[OK] Successfully restarted bot (PID: {new_pid})")
            return 0
        else:
            log("[ERROR] Failed to restart bot")
            return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
