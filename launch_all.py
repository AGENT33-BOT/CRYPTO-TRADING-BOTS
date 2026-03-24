"""
Launch all trading bots simultaneously
"""

import subprocess
import time
import sys

bots = [
    ("Auto Trader Enhanced", "auto_trader_enhanced.py"),
    ("BOSS33 Protection", "boss33_protection_v2.py"),
    ("Signal Scanner 30s", "signal_scanner_30s.py"),
    ("Partial Profit Taker", "partial_profit_taker.py"),
    ("Orphan Order Cleaner", "orphan_order_cleaner.py"),
    # ("Grid Trader", "grid_trader.py"),        # Uncomment to enable
    # ("Funding Arbitrage", "funding_arbitrage.py"),  # Uncomment to enable
]

print("=" * 60)
print("LAUNCHING ALL BYBIT TRADING BOTS")
print("=" * 60)

processes = []

for name, script in bots:
    print(f"\nStarting {name}...")
    try:
        # Start in new window (Windows)
        process = subprocess.Popen(
            ["python", script],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        processes.append((name, process))
        print(f"  PID: {process.pid}")
        time.sleep(2)
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 60)
print(f"All bots launched! Total: {len(processes)}")
print("=" * 60)
print("\nPress Ctrl+C to stop all bots...")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\nStopping all bots...")
    for name, process in processes:
        try:
            process.terminate()
            print(f"  Stopped {name}")
        except:
            pass
    print("All bots stopped.")
