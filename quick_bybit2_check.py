import ccxt
import json

API_KEY = 'An3nB1E8X9X4G2F'
API_SECRET = 'Z5C4D3B2A1F0E9D8C7B6A5F4E3D2C1B0A'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

balance = exchange.fetch_balance()
usdt = balance.get('USDT', {})
print(f"Balance: ${float(usdt.get('total', 0)):.2f} USDT")

positions = exchange.fetch_positions()
active = [p for p in positions if float(p.get('contracts', 0)) != 0]
print(f"Positions: {len(active)}")
for pos in active:
    print(f"  {pos.get('symbol')}: {pos.get('side')} {pos.get('contracts')} @ {pos.get('entryPrice')} | PnL: ${float(pos.get('unrealizedPnl', 0)):+.2f}")
