import psutil
import os
import signal

# Track processes by script name
processes = {
    'mean_reversion_trader.py': [],
    'momentum_trader.py': [],
    'scalping_bot.py': [],
    'grid_trader.py': [],
    'funding_arbitrage.py': [],
    'polymarket_trader.py': [],
    'auto_position_opener.py': [],
}

print("Scanning for Python processes...")
for p in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if p.info['name'] == 'python.exe' or p.info['name'] == 'python':
            cmdline = p.info['cmdline']
            if cmdline:
                cmd_str = ' '.join(cmdline)
                for script in processes.keys():
                    if script in cmd_str:
                        processes[script].append(p.info['pid'])
                        break
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

print("\nCurrent process counts:")
for script, pids in processes.items():
    print(f"  {script}: {len(pids)} instances")

print("\nKilling duplicates (keeping oldest PID for each)...")
for script, pids in processes.items():
    if len(pids) > 1:
        # Sort PIDs - lower PID usually means started earlier
        pids_sorted = sorted(pids)
        keep = pids_sorted[0]  # Keep the oldest
        kill = pids_sorted[1:]  # Kill the rest
        print(f"  {script}: keeping PID {keep}, killing {kill}")
        for pid in kill:
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"    Killed PID {pid}")
            except Exception as e:
                print(f"    Failed to kill PID {pid}: {e}")
    elif len(pids) == 1:
        print(f"  {script}: OK (PID {pids[0]})")
    else:
        print(f"  {script}: NOT RUNNING")

print("\nDone!")