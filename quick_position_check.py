#!/usr/bin/env python3
"""Quick position check"""
import ccxt

exchange = ccxt.bybit({
    'apiKey': 'aLz3ySrF9kMZubmqDR',
    'secret': '8SlpKyX7vleDu1loJiFePGWfnynJRXZXaD2z',
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

print("Fetching positions...")
positions = exchange.fetch_positions()
print(f"Total positions fetched: {len(positions)}")
print("-" * 50)

open_count = 0
for pos in positions:
    contracts = float(pos.get('contracts', 0) or 0)
    symbol = pos.get('symbol', 'N/A')
    side = pos.get('side', 'N/A')
    
    if contracts != 0:
        open_count += 1
        print(f"\n📈 {symbol} {side.upper()}")
        print(f"   Contracts: {contracts}")
        print(f"   Entry: {pos.get('entryPrice')}")
        print(f"   Mark: {pos.get('markPrice')}")
        print(f"   TP: {pos.get('takeProfit')}")
        print(f"   SL: {pos.get('stopLoss')}")
        print(f"   Unrealized PnL: {pos.get('unrealizedPnl')}")

print(f"\n{'='*50}")
print(f"Open positions: {open_count}")
