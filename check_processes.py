import os
import psutil

bots = {
    'mean_reversion': 'mean_reversion_trader.py',
    'momentum': 'momentum_trader.py', 
    'scalping': 'scalping_bot.py',
    'funding': 'funding_arbitrage.py',
    'grid': 'grid_trader.py'
}

print("=== BOT PROCESS STATUS ===")
for name, script in bots.items():
    found = False
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(p.info['cmdline']) if p.info['cmdline'] else ''
            if script in cmdline:
                print(f"[OK] {name.upper()}: RUNNING (PID {p.info['pid']})")
                found = True
                break
        except:
            pass
    if not found:
        status = "DISABLED" if name == 'grid' else "STOPPED"
        print(f"[X] {name.upper()}: {status}")

print(f"\nTotal Python processes: {len([p for p in psutil.process_iter(['name']) if 'python' in p.info['name'].lower()])}")
