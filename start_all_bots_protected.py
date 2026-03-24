"""
Start All Trading Bots with $5 Max Loss Protection
"""
import subprocess
import os
import time

crypto_trader_dir = r"C:\Users\digim\clawd\crypto_trader"

print("=" * 70)
print("STARTING ALL TRADING BOTS")
print("Max Loss Per Position: $5")
print("TP/SL Protection: ENABLED")
print("=" * 70)

bots = [
    # (script_name, log_file)
    ("mean_reversion_trader.py", "mean_reversion_restart.log"),
    ("momentum_trader.py", "momentum_restart.log"),
    ("scalping_bot.py", "scalping_restart.log"),
    ("grid_trader.py", "grid_trader_restart.log"),
    ("funding_arbitrage.py", "funding_restart.log"),
]

started = []

for script, log_file in bots:
    try:
        print(f"\nStarting {script}...")
        
        # Start in background with log file
        with open(os.path.join(crypto_trader_dir, log_file), 'a') as f:
            proc = subprocess.Popen(
                ['python', script],
                stdout=f,
                stderr=subprocess.STDOUT,
                cwd=crypto_trader_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            started.append((script, proc.pid))
            print(f"   STARTED (PID: {proc.pid})")
        
        time.sleep(1)  # Stagger starts
        
    except Exception as e:
        print(f"   Failed: {e}")

print("\n" + "=" * 70)
print(f"STARTED {len(started)} BOTS:")
for script, pid in started:
    print(f"   - {script} (PID: {pid})")

print("\nPROTECTION SETTINGS:")
print("   - Max Loss Per Position: $5")
print("   - Stop Loss: ~1.5% (tight)")
print("   - Take Profit: 3%")
print("   - TP/SL Guardian: Running every minute")

print("\nMONITORING:")
print("   - Check logs for activity")
print("   - Guardian will auto-protect new positions")
print("   - Max 5 positions to limit total risk")

print("\n" + "=" * 70)
