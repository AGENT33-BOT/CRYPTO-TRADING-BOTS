import ccxt

api_key = 'aLz3ySrF9kMZubmqDR'
api_secret = '8SlpKyX7vleDu1loJiFePGWfnynJRXZXaD2z'

ex = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

# Get balance
bal = ex.fetch_balance()
print(f"BYBIT2 BALANCE: ${bal['total']['USDT']:.2f} USDT")
print(f"Free: ${bal['free']['USDT']:.2f}")
print(f"Used: ${bal['used']['USDT']:.2f}")

# Get positions
positions = ex.fetch_positions()
print(f"\nTotal positions: {len(positions)}")
for p in positions:
    if p.get('contracts', 0) > 0:
        print(f"  {p['symbol']}: {p['side']} {p['contracts']} @ ${p['entryPrice']} | PnL: ${p['unrealizedPnl']}")
