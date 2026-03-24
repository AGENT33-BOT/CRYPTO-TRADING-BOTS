#!/usr/bin/env python3
"""Check and close funding arbitrage positions"""
import ccxt
import sys

exchange = ccxt.bybit({
    'apiKey': 'bsK06QDhsagOWwFsXQ',
    'secret': 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa',
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

positions = exchange.fetch_positions()
active = [p for p in positions if float(p.get('contracts', 0)) != 0]

print('=' * 60)
print('ACTIVE POSITIONS')
print('=' * 60)

for p in active:
    symbol = p['symbol']
    side = p['side']
    size = float(p['contracts'])
    entry = float(p.get('entryPrice', 0))
    pnl = float(p.get('unrealizedPnl', 0))
    print(f"{symbol}: {side.upper()} {size} @ ${entry:.4f} | PnL: ${pnl:.2f}")

print('=' * 60)
print(f'Total active positions: {len(active)}')
print('=' * 60)
