import ccxt

ex = ccxt.bybit({
    'apiKey': 'aLz3ySrF9kMZubmqDR',
    'secret': '8SlpKyX7vleDu1loJiFePGWfnynJRXZXaD2z',
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})
bal = ex.fetch_balance()
usdt = bal.get('USDT', {})
print(f"Bybit2 Balance: {usdt.get('free', 0) + usdt.get('used', 0)} USDT")
print(f"  Free: {usdt.get('free', 0)}")
print(f"  Used: {usdt.get('used', 0)}")

# Check positions
positions = ex.fetch_positions()
print(f"\nPositions: {len(positions)}")
for p in positions:
    if float(p.get('contracts', 0)) != 0:
        print(f"  {p['symbol']}: {p['side']} {p['contracts']} @ {p['entryPrice']}")
