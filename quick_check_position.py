import ccxt

API_KEY = 'aLz3ySrF9kMZubmqDR'
API_SECRET = '8SlpKyX7vleDu1loJiFePGWfnynJRXZXaD2z'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

positions = exchange.fetch_positions()
for p in positions:
    contracts = float(p.get('contracts', 0) or 0)
    if contracts != 0:
        print(f"Symbol: {p['symbol']}")
        print(f"Side: {p.get('side')}")
        print(f"Entry: {p.get('entryPrice')}")
        print(f"Contracts: {contracts}")
        print(f"TP: {p.get('takeProfit')}")
        print(f"SL: {p.get('stopLoss')}")
        print(f"PositionIdx: {p.get('positionIdx', 0)}")
        print(f"unrealizedPnl: {p.get('unrealizedPnl')}")
        print('---')
