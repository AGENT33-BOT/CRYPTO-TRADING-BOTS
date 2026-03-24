import os
import sys

log_files = {
    'Bot Monitor': 'bot_monitor.log',
    'Mean Reversion': 'mean_reversion.log', 
    'Momentum': 'momentum_trader.log',
    'Scalping': 'scalping_bot.log',
    'Grid Trading': 'grid_trading.log',
    'Funding Arbitrage': 'funding_arbitrage.log'
}

print("="*60)
print("AGENT33 BOT STATUS CHECK")
print("="*60)

for name, logfile in log_files.items():
    try:
        with open(logfile, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            if lines:
                last_time = None
                for line in reversed(lines):
                    if '2026-' in line or '2025-' in line:
                        parts = line.split(']')[0] if ']' in line else line[:30]
                        last_time = parts.strip()
                        break
                status = 'RUNNING' if len(lines) > 0 else 'NO DATA'
                print(f"\n[+] {name}")
                print(f"    Last entry: {last_time or 'Unknown'}")
                print(f"    Status: {status}")
            else:
                print(f"\n[!] {name}")
                print(f"    Status: EMPTY LOG")
    except Exception as e:
        print(f"\n[!] {name}")
        print(f"    Status: ERROR - {e}")

print("\n" + "="*60)
