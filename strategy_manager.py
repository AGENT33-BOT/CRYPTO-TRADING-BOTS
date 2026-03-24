"""
Strategy Launcher - Start/Stop all trading bots
Usage: python strategy_manager.py [start|stop|status] [strategy_name|all]
"""

import subprocess
import psutil
import sys
import os
import json
import time

# Strategy definitions
STRATEGIES = {
    'grid': {
        'file': 'grid_trader.py',
        'log': 'grid_trading.log',
        'description': 'Grid Trading Bot'
    },
    'funding': {
        'file': 'funding_arbitrage.py',
        'log': 'funding_arbitrage.log',
        'description': 'Funding Arbitrage Bot'
    },
    'mean_reversion': {
        'file': 'mean_reversion_trader.py',
        'log': 'mean_reversion.log',
        'description': 'Mean Reversion Trader (BB+RSI)'
    },
    'momentum': {
        'file': 'momentum_trader.py',
        'log': 'momentum_trader.log',
        'description': 'Momentum Trader (EMA)'
    },
    'scalping': {
        'file': 'scalping_bot.py',
        'log': 'scalping_bot.log',
        'description': 'Scalping Bot (1m)'
    },
    'auto_opener': {
        'file': 'auto_position_opener.py',
        'log': 'auto_opener.log',
        'description': 'Auto Position Opener'
    }
}

PID_FILE = 'strategy_pids.json'

def load_pids():
    try:
        if os.path.exists(PID_FILE):
            with open(PID_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_pids(pids):
    with open(PID_FILE, 'w') as f:
        json.dump(pids, f, indent=2)

def is_process_running(pid):
    try:
        process = psutil.Process(pid)
        return process.is_running()
    except:
        return False

def start_strategy(name):
    """Start a strategy"""
    if name not in STRATEGIES:
        print(f"[ERROR] Unknown strategy: {name}")
        return False
    
    strategy = STRATEGIES[name]
    pids = load_pids()
    
    # Check if already running
    if name in pids and is_process_running(pids[name]):
        print(f"[OK] {name} already running (PID: {pids[name]})")
        return True
    
    # Start the process
    try:
        print(f"[STARTING] {name}...")
        process = subprocess.Popen(
            ['python', strategy['file']],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        pids[name] = process.pid
        save_pids(pids)
        
        print(f"[OK] {name} started (PID: {process.pid})")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to start {name}: {e}")
        return False

def stop_strategy(name):
    """Stop a strategy"""
    pids = load_pids()
    
    if name not in pids:
        print(f"[WARN] {name} not in PID file")
        return False
    
    pid = pids[name]
    
    try:
        if is_process_running(pid):
            process = psutil.Process(pid)
            process.terminate()
            process.wait(timeout=5)
            print(f"[STOPPED] {name} (PID: {pid})")
        else:
            print(f"[WARN] {name} not running (PID: {pid})")
        
        del pids[name]
        save_pids(pids)
        return True
    except Exception as e:
        print(f"[ERROR] Error stopping {name}: {e}")
        return False

def get_status():
    """Get status of all strategies"""
    print("=" * 70)
    print("STRATEGY STATUS")
    print("=" * 70)
    
    pids = load_pids()
    running = 0
    stopped = 0
    
    for name, strategy in STRATEGIES.items():
        if name in pids and is_process_running(pids[name]):
            status = "[RUNNING]"
            pid_info = f"(PID: {pids[name]})"
            running += 1
        else:
            status = "[STOPPED]"
            pid_info = ""
            if name in pids:
                stopped += 1
                # Clean up dead PIDs
                del pids[name]
    
        print(f"{name:20} {status:12} {pid_info}")
        print(f"  - {strategy['description']}")
    
    if stopped > 0:
        save_pids(pids)
    
    print("=" * 70)
    print(f"Running: {running} | Stopped: {len(STRATEGIES) - running}")
    print("=" * 70)

def show_logs(name, lines=20):
    """Show last N lines of log file"""
    if name not in STRATEGIES:
        print(f"[ERROR] Unknown strategy: {name}")
        return
    
    log_file = STRATEGIES[name]['log']
    
    try:
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                last_lines = all_lines[-lines:]
                print(f"\nLast {len(last_lines)} lines from {log_file}:")
                print("-" * 70)
                for line in last_lines:
                    print(line.rstrip())
                print("-" * 70)
        else:
            print(f"[WARN] Log file not found: {log_file}")
    except Exception as e:
        print(f"[ERROR] Error reading logs: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python strategy_manager.py [start|stop|status|logs] [strategy|all]")
        print("\nStrategies:")
        for name, info in STRATEGIES.items():
            print(f"  - {name:15} {info['description']}")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'status':
        get_status()
        return
    
    if len(sys.argv) < 3:
        print("[ERROR] Please specify a strategy name or 'all'")
        return
    
    target = sys.argv[2].lower()
    
    if command == 'logs':
        lines = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        show_logs(target, lines)
        return
    
    if target == 'all':
        if command == 'start':
            print("Starting all strategies...")
            for name in STRATEGIES:
                start_strategy(name)
                time.sleep(0.5)
        elif command == 'stop':
            print("Stopping all strategies...")
            for name in STRATEGIES:
                stop_strategy(name)
        get_status()
    else:
        if command == 'start':
            start_strategy(target)
        elif command == 'stop':
            stop_strategy(target)
        else:
            print(f"[ERROR] Unknown command: {command}")

if __name__ == "__main__":
    main()
