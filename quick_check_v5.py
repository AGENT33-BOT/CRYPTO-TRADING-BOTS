#!/usr/bin/env python3
"""Quick position check using v5 API"""
import ccxt
import json

exchange = ccxt.bybit({
    'apiKey': 'aLz3ySrF9kMZubmqDR',
    'secret': '8SlpKyX7vleDu1loJiFePGWfnynJRXZXaD2z',
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

# Try v5 endpoint directly
print("Trying v5 position API...")

try:
    response = exchange.private_get_v5_position_closed_pnl({
        'category': 'linear',
        'limit': 10
    })
    print("Closed PnL response:")
    print(json.dumps(response, indent=2))
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*50 + "\n")

# Try fetch_positions again with different approach
try:
    # Try fetching positions with explicit params
    positions = exchange.fetch_positions({'settleCoin': 'USDT'})
    print(f"fetch_positions (with settleCoin=USDT): {len(positions)} positions")
    for p in positions:
        print(f"  {p['symbol']}: {p.get('side')} {p.get('contracts')}")
except Exception as e:
    print(f"Error with settleCoin: {e}")

print("\n" + "="*50 + "\n")

# Try default fetch
try:
    positions = exchange.fetch_positions()
    print(f"fetch_positions (default): {len(positions)} positions")
    for p in positions:
        print(f"  {p['symbol']}: {p.get('side')} {p.get('contracts')}")
except Exception as e:
    print(f"Error default: {e}")

# Check balance too
print("\n" + "="*50)
print("Checking balance...")
try:
    balance = exchange.fetch_balance()
    print(f"USDT: {balance.get('USDT', {})}")
except Exception as e:
    print(f"Balance error: {e}")
