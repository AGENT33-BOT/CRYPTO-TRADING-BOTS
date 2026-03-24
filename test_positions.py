import ccxt
import os

API_KEY = 'aLz3ySrF9kMZubmqDR'
API_SECRET = '8SlpKyX7vleDu1loJiFePGWfnynJRXZXaD2z'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

# Try ccxt fetch_positions
positions = exchange.fetch_positions()
print(f'Total positions from fetch_positions: {len(positions)}')
for p in positions:
    size = float(p.get('contracts', 0) or p.get('size', 0) or 0)
    if size != 0:
        print(f"  {p['symbol']}: size={size}, side={p.get('side')}, TP={p.get('takeProfit')}, SL={p.get('stopLoss')}")

# Try direct API with settleCoin
print('\n--- Direct API ---')
resp = exchange.private_get_v5_position_list({'category': 'linear', 'settleCoin': 'USDT'})
print(f"retCode: {resp.get('retCode')}")
print(f"Number of positions: {len(resp.get('result', {}).get('list', []))}")
for pos in resp.get('result', {}).get('list', []):
    size = pos.get('size', '0')
    print(f"  {pos.get('symbol')}: size={size}, side={pos.get('side')}, TP={pos.get('takeProfit')}, SL={pos.get('stopLoss')}")
