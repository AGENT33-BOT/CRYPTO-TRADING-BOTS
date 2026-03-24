#!/usr/bin/env python3
"""
AGGRESSIVE SPOT BLOCKER - Prevents ANY spot trading
This script runs continuously and kills any process that tries to create spot positions
"""
import psutil
import time
import os
import sys
from datetime import datetime

# Add parent dir for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BLOCKED_PROCESSES = [
    'funding_arbitrage.py',  # OLD bot that buys spot
]

LOG_FILE = 'aggressive_spot_blocker.log'

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
                cmdline = proc.info.get('cmdline', [])
                if cmdline:
                    script = ' '.join(cmdline) if isinstance(cmdline, list) else str(cmdline)
                    
                    for blocked in BLOCKED_PROCESSES:
                        if blocked in script:
                            # Kill it!
                            try:
                                proc.kill()
                                killed.append((proc.info['pid'], script))
                                log(f"KILLED SPOT BOT: PID {proc.info['pid']} - {script[:80]}")
                                
                                # Also sell any spot that was created
                                log("Running spot seller...")
                                os.system('python sell_all_spot.py')
                            except:
                                pass
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    return killed

def check_spot_positions():
    """Check if any spot positions exist"""
    try:
        import ccxt
        exchange = ccxt.bybit({
            'apiKey': 'bsK06QDhsagOWwFsXQ',
            'secret': 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa',
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        
        balance = exchange.fetch_balance()
        spot_coins = []
        
        for coin, data in balance.items():
            if coin != 'USDT' and coin != 'info' and coin != 'free' and coin != 'used' and coin != 'total':
                total = float(data.get('total', 0))
                if total > 0.001:  # Has meaningful balance
                    spot_coins.append(coin)
        
        if spot_coins:
            log(f"ALERT: Found spot holdings: {', '.join(spot_coins)}")
            log("Auto-selling...")
            os.system('python sell_all_spot.py')
            return True
        return False
        
    except Exception as e:
        log(f"Error checking spot: {e}")
        return False

def main():
    log("\n" + "=" * 60)
    log("AGGRESSIVE SPOT BLOCKER STARTED")
    log("Killing any funding_arbitrage.py processes")
    log("Checking every 10 seconds...")
    log("=" * 60 + "\n")
    
    # Initial cleanup
    log("Initial cleanup...")
    check_and_kill_spot_bots()
    check_spot_positions()
    
    while True:
        killed = check_and_kill_spot_bots()
        had_spot = check_spot_positions()
        
        if killed:
            log(f"BLOCKED {len(killed)} SPOT BOTS")
            for pid, script in killed:
                log(f"   Killed: {script[:60]}...")
        elif had_spot:
            log("Sold spot holdings detected")
        else:
            log("No spot activity detected")
        
        # Check every 10 seconds
        time.sleep(10)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log("\nSpot blocker stopped")
