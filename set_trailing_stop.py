#!/usr/bin/env python3
"""
Set Trailing Stop Loss for all Bybit positions at 1%
"""

import os
from pybit.unified_trading import HTTP
from dotenv import load_dotenv

load_dotenv()

# Initialize session
session = HTTP(
    api_key=os.getenv('BYBIT_API_KEY'),
    api_secret=os.getenv('BYBIT_SECRET'),
    testnet=False
)

TRAILING_PERCENT = 1.0  # 1% trailing stop

print(f"Setting {TRAILING_PERCENT}% Trailing Stop for all positions\n")

# Get positions
positions = session.get_positions(
    category='linear',
    settleCoin='USDT'
)['result']['list']

active_positions = [p for p in positions if float(p['size']) > 0]

if not active_positions:
    print("No active positions found.")
    exit()

print(f"Found {len(active_positions)} position(s):\n")

for pos in active_positions:
    symbol = pos['symbol']
    side = pos['side']
    size = pos['size']
    entry = float(pos['avgPrice'])
    
    print(f"[+] {symbol} {side} {size} @ ${entry:.2f}")
    
    try:
        # Set trailing stop
        # Trailing stop triggers when price moves favorably by activation price
        # Then trails by the specified distance
        
        result = session.set_trading_stop(
            category='linear',
            symbol=symbol,
            trailingStop=str(TRAILING_PERCENT),
            positionIdx=0  # One-way mode
        )
        
        if result['retCode'] == 0:
            print(f"   [OK] Trailing stop set: {TRAILING_PERCENT}%\n")
        else:
            print(f"   [WARN] {result['retMsg']}\n")
            
    except Exception as e:
        error_msg = str(e).encode('ascii', 'ignore').decode('ascii')
        print(f"   [ERR] {error_msg[:80]}\n")

print("Done! Trailing stops activated.")
