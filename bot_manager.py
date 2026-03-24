"""
Bot Manager Script for Agent33 Trading System
Handles safe restarts, file lock cleanup, and bot health monitoring
"""

import subprocess
import os
import sys
import time
import signal
import psutil
from datetime import datetime

# Bot configurations
BOTS = {
    'scalping': {
        'script': 'scalping_bot.py',
        'lock_file': None,
        'log_file': 'scalping_bot.log',
    },
    'grid': {
        'script': 'grid_trader.py',
        'lock_file': 'grid_trader.lock',
        'log_file': 'grid_trading.log',
    },
    'mean_reversion': {
        'script': 'mean_reversion_trader.py',
        'lock_file': None,
        'log_file': 'mean_reversion.log',
    },
    'momentum': {
        'script': 'momentum_trader.py',
        'lock_file': None,
        'log_file': 'momentum_trader.log',
    },
    'crypto_com': {
        'script': 'crypto_com_agent.py',
        'lock_file': None,
        'log_file': 'crypto_com_trading.log',
    },
}

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # Encode/decode to handle unicode on Windows
    try:
        print(f"[{timestamp}] {msg}")
    except UnicodeEncodeError:
        safe_msg = msg.encode('ascii', 'replace').decode('ascii')
        print(f"[{timestamp}] {safe_msg}")

def find_bot_process(bot_name):
    """Find running bot process by script name"""
    script_name = BOTS[bot_name]['script']
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline', [])
            if cmdline and script_name in ' '.join(cmdline):
                return proc.info['pid']
        except:
            pass
    return None

def kill_bot(bot_name):
    """Kill bot process and cleanup lock files"""
    pid = find_bot_process(bot_name)
    
    if pid:
        log(f"Killing {bot_name} bot (PID: {pid})...")
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)
            
            # Force kill if still running
            if psutil.pid_exists(pid):
                os.kill(pid, signal.SIGKILL)
                time.sleep(1)
        except Exception as e:
            log(f"Warning: Error killing process: {e}")
    
    # Clean up lock file if exists
    lock_file = BOTS[bot_name].get('lock_file')
    if lock_file and os.path.exists(lock_file):
        try:
            os.remove(lock_file)
            log(f"Removed lock file: {lock_file}")
        except Exception as e:
            log(f"Warning: Could not remove lock file: {e}")

def start_bot(bot_name):
    """Start a bot in the background"""
    script = BOTS[bot_name]['script']
    
    if not os.path.exists(script):
        log(f"❌ {bot_name}: Script not found: {script}")
        return False
    
    log(f"Starting {bot_name} bot...")
    
    try:
        # Use pythonw on Windows for no console window
        if sys.platform == 'win32':
            subprocess.Popen(
                ['python', script],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
        else:
            subprocess.Popen(
                ['python3', script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
        
        time.sleep(2)
        
        # Verify it started
        pid = find_bot_process(bot_name)
        if pid:
            log(f"✅ {bot_name} started (PID: {pid})")
            return True
        else:
            log(f"❌ {bot_name} failed to start")
            return False
            
    except Exception as e:
        log(f"❌ {bot_name} error: {e}")
        return False

def restart_bot(bot_name):
    """Restart a bot safely"""
    log(f"\n{'='*50}")
    log(f"Restarting {bot_name}...")
    log(f"{'='*50}")
    
    # Kill existing
    kill_bot(bot_name)
    time.sleep(1)
    
    # Start fresh
    return start_bot(bot_name)

def restart_all():
    """Restart all bots"""
    log("\n" + "="*60)
    log("RESTARTING ALL TRADING BOTS")
    log("="*60 + "\n")
    
    results = {}
    for bot_name in BOTS.keys():
        results[bot_name] = restart_bot(bot_name)
        time.sleep(2)  # Stagger starts
    
    log("\n" + "="*60)
    log("RESTART SUMMARY")
    log("="*60)
    for bot_name, success in results.items():
        status = "✅" if success else "❌"
        log(f"{status} {bot_name}")
    
    return results

def check_bot_health(bot_name):
    """Check if bot is healthy (running + recent log activity)"""
    pid = find_bot_process(bot_name)
    
    if not pid:
        return False, "Not running"
    
    # Check log file for recent activity
    log_file = BOTS[bot_name].get('log_file')
    if log_file and os.path.exists(log_file):
        try:
            mtime = os.path.getmtime(log_file)
            age_minutes = (time.time() - mtime) / 60
            
            if age_minutes > 15:
                return False, f"Stale logs ({age_minutes:.0f}m old)"
        except:
            pass
    
    return True, f"Running (PID: {pid})"

def health_check():
    """Check health of all bots"""
    log("\n" + "="*60)
    log("BOT HEALTH CHECK")
    log("="*60 + "\n")
    
    for bot_name in BOTS.keys():
        healthy, status = check_bot_health(bot_name)
        icon = "✅" if healthy else "❌"
        log(f"{icon} {bot_name}: {status}")
    
    log("")

def fix_file_locks():
    """Clean up all stale lock files"""
    log("\n" + "="*60)
    log("CLEANING UP STALE LOCK FILES")
    log("="*60 + "\n")
    
    cleaned = 0
    for bot_name, config in BOTS.items():
        lock_file = config.get('lock_file')
        if lock_file and os.path.exists(lock_file):
            try:
                os.remove(lock_file)
                log(f"✅ Removed: {lock_file}")
                cleaned += 1
            except Exception as e:
                log(f"❌ Could not remove {lock_file}: {e}")
    
    if cleaned == 0:
        log("No stale lock files found")
    
    log("")

def main():
    if len(sys.argv) < 2:
        print("Usage: python bot_manager.py <command> [bot_name]")
        print("")
        print("Commands:")
        print("  restart <bot>     - Restart specific bot")
        print("  restart-all       - Restart all bots")
        print("  stop <bot>        - Stop specific bot")
        print("  health            - Check bot health")
        print("  fix-locks         - Clean up stale lock files")
        print("")
        print("Available bots:", ', '.join(BOTS.keys()))
        return
    
    command = sys.argv[1].lower()
    
    if command == 'restart':
        if len(sys.argv) < 3:
            print("Error: Please specify bot name")
            return
        bot_name = sys.argv[2]
        if bot_name not in BOTS:
            print(f"Error: Unknown bot '{bot_name}'")
            print(f"Available: {', '.join(BOTS.keys())}")
            return
        restart_bot(bot_name)
    
    elif command == 'restart-all':
        restart_all()
    
    elif command == 'stop':
        if len(sys.argv) < 3:
            print("Error: Please specify bot name")
            return
        bot_name = sys.argv[2]
        if bot_name not in BOTS:
            print(f"Error: Unknown bot '{bot_name}'")
            return
        kill_bot(bot_name)
        log(f"Stopped {bot_name}")
    
    elif command == 'health':
        health_check()
    
    elif command == 'fix-locks':
        fix_file_locks()
    
    else:
        print(f"Unknown command: {command}")
        print("Run without arguments for help")

if __name__ == '__main__':
    main()
