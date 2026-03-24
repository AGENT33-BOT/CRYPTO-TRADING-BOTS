import ccxt

# Bybit2 spot account
api_key = 'aLz3ySrF9kMZubmqDR'
api_secret = '8SlpKyX7vleDu1loJiFePGWfnynJRXZXaD2z'

ex = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
})

# Get spot balance
bal = ex.fetch_balance()
print("=" * 50)
print("SPOT POSITIONS TO SELL")
print("=" * 50)

positions_to_sell = []
for currency, amount in bal['total'].items():
    if amount and amount > 0.0001 and currency != 'USDT':
        free = bal['free'].get(currency, 0)
        if free > 0.0001:
            print(f"{currency}: {free}")
            positions_to_sell.append((currency, free))

if not positions_to_sell:
    print("No spot positions to sell!")
else:
    print(f"\nSelling {len(positions_to_sell)} positions...")
    for symbol, amount in positions_to_sell:
        try:
            # Create market sell order
            order = ex.create_order(
                symbol=f"{symbol}/USDT",
                type='market',
                side='sell',
                amount=amount
            )
            print(f"✅ SOLD: {symbol} {amount}")
        except Exception as e:
            print(f"❌ ERROR selling {symbol}: {e}")
