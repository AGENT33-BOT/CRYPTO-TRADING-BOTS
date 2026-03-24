import ccxt

# Main Bybit account
api_key = 'bsK06QDhsagOWwFsXQ'
api_secret = 'VjfKDmG44eMyO7X41x5cWf8Mo1I8SXYgCqJ7'

ex = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
})

# Get spot balance
bal = ex.fetch_balance()
print("=" * 50)
print("BYBIT SPOT WALLET (MAIN)")
print("=" * 50)

for currency, amount in bal['total'].items():
    if amount and amount > 0.0001:
        free = bal['free'].get(currency, 0)
        used = bal['used'].get(currency, 0)
        print(f"{currency}: {amount:.6f} (Free: {free:.6f}, Used: {used:.6f})")

print(f"\nTotal USDT: {bal['total'].get('USDT', 0):.2f}")
