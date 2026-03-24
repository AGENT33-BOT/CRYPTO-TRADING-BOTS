"""
Start all ML trading bots with new 20% position size
"""

import subprocess
import sys
import time

symbols = [
    'ETH/USDT:USDT',
    'NEAR/USDT:USDT',
    'DOGE/USDT:USDT'
]

print("Starting ML Trading Bots (20% position size)...")
print("="*60)

for symbol in symbols:
    safe_symbol = symbol.replace('/', '_')
    log_file = f'ml_bot_{safe_symbol}.log'
    
    # Start bot
    process = subprocess.Popen(
        [sys.executable, 'ml_trader_live.py', '--symbol', symbol],
        stdout=open(log_file, 'a'),
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    
    print(f"Started {symbol} (PID: {process.pid})")
    time.sleep(2)

print("="*60)
print("All 3 bots running with 20% position size!")
print("New trades will use larger position sizes.")
