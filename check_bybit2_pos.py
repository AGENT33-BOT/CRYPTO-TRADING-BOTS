import ccxt
exchange = ccxt.bybit({
    'apiKey': 'aLz3ySrF9kMZubmqDR',
    'secret': '8SlpKyX7vleDu1loJiFePGWfnynJRXZXaD2z',
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})
exchange.load_markets()
positions = exchange.fetch_positions()
print('BYBIT2 POSITIONS:')
for p in positions:
    if float(p['contracts']) != 0:
        print(f"Symbol: {p['symbol']}")
        print(f"  Side: {p['side']}")
        print(f"  Size: {p['contracts']}")
        print(f"  Entry: {p['entryPrice']}")
        print(f"  TP: {p.get('takeProfitPrice', 'NOT SET')}")
        print(f"  SL: {p.get('stopLossPrice', 'NOT SET')}")
        print()
