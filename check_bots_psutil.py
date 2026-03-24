import psutil
import os

print("=== Trading Bot Process Check ===\n")

trading_bots = {
    'mean_reversion_trader.py': 'Mean Reversion Bot (Main)',
    'momentum_trader.py': 'Momentum Bot (Main)',
    'scalping_bot.py': 'Scalping Bot (Main)',
    'grid_trader.py': 'Grid Trading Bot',
    'funding_arbitrage.py': 'Funding Arbitrage Bot',
    'bybit2_mean_reversion.py': 'Bybit2 Mean Reversion',
    'bybit2_momentum.py': 'Bybit2 Momentum',
    'ensure_tp_sl.py': 'TP/SL Guardian (Main)',
    'bybit2_ensure_tp_sl.py': 'TP/SL Guardian (Bybit2)',
}

found_bots = {}

for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if proc.info['name'] == 'python.exe':
            cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
            for script, name in trading_bots.items():
                if script in cmdline:
                    found_bots[script] = {
                        'name': name,
                        'pid': proc.info['pid'],
                    }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

print("[OK] RUNNING BOTS:")
for script, info in found_bots.items():
    print(f"  [OK] {info['name']} (PID: {info['pid']})")

print("\n[MISSING] NOT RUNNING:")
for script, name in trading_bots.items():
    if script not in found_bots:
        print(f"  [X] {name}")

print(f"\n=== Summary ===")
print(f"Running: {len(found_bots)} / {len(trading_bots)}")
