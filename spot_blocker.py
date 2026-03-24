#!/usr/bin/env python3
"""
SPOT ORDER BLOCKER - Prevent Any Spot Trading
This script runs continuously and kills any process that tries to create spot positions
"""
import psutil
import time
import os
from datetime import datetime

BLOCKED_PROCESSES = [
    'funding_arbitrage.py',  # OLD bot that buys spot
]

LOG_FILE = 'spot_blocker.log'

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')

def check_and_kill_spot_bots():
    """Check for and kill any spot-trading bots"""
    killed = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python.exe':
                cmdline = proc.info['cmdline']
                if cmdline and len(cmdline) > 1:
                    script = cmdline[1] if len(cmdline) > 1 else ""
                    
                    for blocked in BLOCKED_PROCESSES:
                        if blocked in script:
                            # Kill it!
                            try:
                                proc.kill()
                                killed.append((proc.info['pid'], script))
                                log(f"🚨 KILLED SPOT BOT: PID {proc.info['pid']} - {script}")
                            except:
                                pass
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    return killed

def main():
    log("=" * 60)
    log("🛡️ SPOT ORDER BLOCKER STARTED")
    log("Monitoring for spot-trading bots...")
    log("=" * 60)
    
    while True:
        killed = check_and_kill_spot_bots()
        
        if killed:
            log(f"🚨 BLOCKED {len(killed)} SPOT BOTS")
            for pid, script in killed:
                log(f"   Killed: {script} (PID: {pid})")
            
            # Also sell any spot that was created
            log("🔄 Running spot seller...")
            os.system('python sell_all_spot.py')
        else:
            log("✅ No spot bots detected")
        
        # Check every 30 seconds
        time.sleep(30)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log("\n🛑 Spot blocker stopped")
