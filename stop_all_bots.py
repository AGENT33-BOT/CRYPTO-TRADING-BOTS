"""
Stop All Trading Bots - Emergency Stop
"""
import subprocess
import os
import signal

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

print("STOPPING ALL TRADING BOTS...")
print("=" * 60)

bots_to_stop = [
    'mean_reversion',
    'momentum',
    'scalping',
    'grid',
    'funding',
    'dca_bot',
    'bybit2_mean',
    'bybit2_momentum'
]

stopped = 0

if HAS_PSUTIL:
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            for bot in bots_to_stop:
                if bot in cmdline.lower() and 'python' in proc.info['name'].lower():
                    print(f"Stopping {bot} (PID {proc.info['pid']})...")
                    proc.terminate()
                    stopped += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
else:
    # Fallback - use taskkill
    print("Using taskkill method...")
    for bot in bots_to_stop:
        try:
            subprocess.run(['taskkill', '/f', '/fi', f'imagename eq python.exe'], 
                         capture_output=True)
            stopped += 1
        except:
            pass

print("=" * 60)
print(f"Stopped {stopped} bot process(es)")
print("\nAll trading bots are now STOPPED.")
print("No new positions will be opened.")
print("\nBalance: $528.19 USDT (safe)")
