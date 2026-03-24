import psutil
import subprocess
import sys
import datetime

# Check for auto_position_opener.py processes
processes = []
for p in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        cmdline = ' '.join(p.info['cmdline'] or [])
        if 'auto_position_opener.py' in cmdline:
            processes.append(p)
    except:
        pass

# Log file
log_file = 'opener_monitor.log'
timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

with open(log_file, 'a') as f:
    f.write(f"[{timestamp}] Monitor check started\n")
    
    if processes:
        f.write(f"[{timestamp}] Found {len(processes)} auto_position_opener process(es):\n")
        for p in processes:
            cmdline = ' '.join(p.info['cmdline'] or [])
            f.write(f"[{timestamp}]   PID {p.info['pid']}: {cmdline}\n")
        print(f"[OK] auto_position_opener.py is running (PID: {processes[0].info['pid']})")
    else:
        f.write(f"[{timestamp}] auto_position_opener.py NOT running - restarting...\n")
        print("[WARN] auto_position_opener.py not running - restarting...")
        
        # Start the process
        try:
            subprocess.Popen(
                [sys.executable, 'auto_position_opener.py'],
                cwd=r'C:\Users\digim\clawd\crypto_trader',
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            f.write(f"[{timestamp}] Successfully restarted auto_position_opener.py\n")
            print("[OK] auto_position_opener.py restarted successfully")
        except Exception as e:
            f.write(f"[{timestamp}] Failed to restart: {e}\n")
            print(f"[ERROR] Failed to restart: {e}")
    
    f.write(f"[{timestamp}] Monitor check completed\n\n")

print(f"[INFO] Logged to {log_file}")
