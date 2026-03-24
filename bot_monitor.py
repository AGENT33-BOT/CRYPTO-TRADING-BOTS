"""
Bot Monitor - Auto-restart all trading bots if they stop
Runs every 5 minutes via cron
Sends crypto alerts ONLY to @Agent33_tradingbot

FIXED: Use psutil for reliable process detection, prevent duplicates
"""
import subprocess
import time
import os
import sys
import requests
import psutil
from datetime import datetime
import json

# Telegram: Crypto alerts go ONLY to trading bot
TRADING_BOT_TOKEN = "8586893914:AAEIuNFlGNbhDeUQ-eXUOmTm0KHw_-aOtuI"
TRADING_CHAT_ID = "5804173449"

# State file to track running bots and prevent duplicates
STATE_FILE = "C:\\Users\\digim\\clawd\\crypto_trader\\bot_monitor_state.json"

def load_state():
    """Load previous state to prevent duplicate restarts"""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_state(state):
    """Save state to prevent duplicate restarts"""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
    except:
        pass

def send_trading_alert(message):
    """Send crypto alert to trading bot only"""
    try:
        url = f"https://api.telegram.org/bot{TRADING_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TRADING_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        requests.post(url, json=payload, timeout=10)
        print("  [OK] Alert sent to @Agent33_tradingbot")
    except Exception as e:
        print(f"  [WARN] Trading bot alert failed: {e}")

def find_procs_by_name(name):
    """Find processes matching name in command line using psutil"""
    matching = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'python' in proc.info['name'].lower() and name in cmdline:
                matching.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return matching

def get_process_pids(script_keyword):
    """Get list of PIDs for a script"""
    return find_procs_by_name(script_keyword)

def check_bot_status():
    """Check if all bots are running (exactly 1 instance each)"""
    bots = {
        # 'grid': 'grid_trader',  # DISABLED
        'funding': 'funding_arbitrage',
        'mean_reversion': 'mean_reversion_trader',
        'momentum': 'momentum_trader',
        'scalping': 'scalping_bot'
    }
    
    status = {}
    
    for bot_key, script_name in bots.items():
        pids = get_process_pids(script_name)
        count = len(pids)
        
        # Bot is running if exactly 1 instance (not 0, not >1)
        is_running = count == 1
        
        # Check for duplicates - if >1, we need to kill extras
        has_duplicates = count > 1
        
        status[bot_key] = {
            'running': is_running,
            'count': count,
            'pids': pids,
            'has_duplicates': has_duplicates,
            'script': script_name
        }
        
        # Simple status output
        if has_duplicates:
            print(f"  {bot_key}: DUPLICATES ({count} PIDs: {pids})")
        elif is_running:
            print(f"  {bot_key}: running (PID {pids[0]})")
        else:
            print(f"  {bot_key}: NOT RUNNING")
    
    return status

def kill_extras(bot_key, script_name, pids):
    """Kill duplicate processes, keeping only the first one"""
    if len(pids) <= 1:
        return []
    
    # Keep first PID, kill the rest
    keep_pid = pids[0]
    kill_pids = pids[1:]
    
    killed = []
    for pid in kill_pids:
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            killed.append(pid)
            print(f"  [KILLED] Duplicate {bot_key} PID {pid}")
        except Exception as e:
            print(f"  [WARN] Failed to kill PID {pid}: {e}")
    
    return killed

def kill_all_for_script(script_name):
    """Kill ALL processes for a script (used for restart)"""
    pids = get_process_pids(script_name)
    for pid in pids:
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            print(f"  [TERMINATED] {script_name} PID {pid}")
        except Exception as e:
            pass
    time.sleep(1)

def restart_bot(bot_name, script_name):
    """Restart a bot (only if not running)"""
    # First check if already running
    pids = get_process_pids(script_name)
    count = len(pids)
    
    if count >= 1:
        print(f"  [SKIP] {bot_name} already running ({count} instances)")
        return False
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting {bot_name}...")
    
    try:
        # Kill any stray processes first
        kill_all_for_script(script_name)
        
        # Start new process
        subprocess.Popen(
            ['powershell', '-Command',
             rf'cd C:\Users\digim\clawd\crypto_trader; Start-Process python -ArgumentList "{script_name}" -WindowStyle Hidden'],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        
        print(f"  [OK] {bot_name} started successfully")
        return True
        
    except Exception as e:
        print(f"  [FAIL] Failed to start {bot_name}: {e}")
        return False

def log_restart(action_type, bots):
    """Log action to file"""
    log_file = "C:\\Users\\digim\\clawd\\crypto_trader\\bot_monitor.log"
    with open(log_file, "a", encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {action_type}: {', '.join(bots)}\n")

def main():
    """Main monitoring loop"""
    print("="*60)
    print("BOT MONITOR - Auto-Restart Service (v4 - psutil)")
    print("Crypto alerts: @Agent33_tradingbot ONLY")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print()
    
    # Check current status
    status = check_bot_status()
    print()
    
    killed_duplicates = []
    restarted = []
    
    # First: kill any duplicate processes
    for bot_key, info in status.items():
        if info['has_duplicates']:
            killed = kill_extras(bot_key, info['script'], info['pids'])
            if killed:
                killed_duplicates.append(f"{bot_key} ({len(killed)} duplicates)")
    
    if killed_duplicates:
        print()
        print(f"KILLED DUPLICATES: {', '.join(killed_duplicates)}")
        log_restart("Killed duplicates", killed_duplicates)
        
        # Send alert about duplicates
        msg = f"🧹 <b>Duplicate Bots Killed</b>\n\n"
        msg += f"<b>Bots:</b> {', '.join(killed_duplicates)}\n"
        msg += f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ET"
        send_trading_alert(msg)
    
    # Second: restart stopped bots
    bot_names = {
        'funding': 'Funding Arbitrage Bot', 
        'mean_reversion': 'Mean Reversion Bot',
        'momentum': 'Momentum Bot',
        'scalping': 'Scalping Bot'
    }
    
    for bot_key, info in status.items():
        if not info['running'] and not info['has_duplicates']:
            # Only restart if not running AND no duplicates were found
            if restart_bot(bot_names[bot_key], info['script']):
                restarted.append(bot_names[bot_key])
    
    if restarted:
        print()
        print(f"RESTARTED: {', '.join(restarted)}")
        log_restart("Restarted", restarted)
        
        # Send alert
        msg = f"🔄 <b>Bots Restarted</b>\n\n"
        msg += f"<b>Bots:</b> {', '.join(restarted)}\n"
        msg += f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ET"
        send_trading_alert(msg)
    
    # Final status
    print()
    print("FINAL STATUS:")
    final_status = check_bot_status()
    for bot_key, info in final_status.items():
        if info['has_duplicates']:
            print(f"  {bot_key}: HAD DUPLICATES (fix pending)")
        elif info['running']:
            print(f"  {bot_key}: RUNNING")
        else:
            print(f"  {bot_key}: STOPPED")
    
    if not killed_duplicates and not restarted:
        print("  All bots running normally (1 instance each)")
    
    print()
    print("="*60)

if __name__ == "__main__":
    main()
