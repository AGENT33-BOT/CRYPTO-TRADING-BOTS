#!/usr/bin/env python3
"""Quick position check for main Bybit account"""
import ccxt

# Main Bybit account
exchange = ccxt.bybit({
    'apiKey': 'oW5V4VrxKZCYGHgUVN',
    'secret': 'cJxVCgR4FTCf6FxAU7wY7wY7wY7wY7wY7wY',
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

print('Checking main Bybit account positions...')
positions = exchange.fetch_positions()
print(f'Total: {len(positions)}')

for p in positions:
    size = p.get('contracts') or 0
    if size != 0:
        print(f"  {p['symbol']} | {p.get('side')} | {size} @ {p.get('entryPrice')}")
        print(f"    TP: {p.get('takeProfit')} | SL: {p.get('stopLoss')}")
