import ccxt

# Bybit2 - check both spot and futures
api_key = 'aLz3ySrF9kMZubmqDR'
api_secret = '8SlpKyX7vleDu1loJiFePGWfnynJRXZXaD2z'

# Spot wallet
ex_spot = ccxt.bybit({
    'apiKey': api_key,
    'api_secret': api_secret,
    'enableRateLimit': True,
})

# Futures wallet  
ex_futures = ccxt.bybit({
    'apiKey': api_key,
    'api_secret': api_secret,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

print("=" * 50)
print("BYBIT2 SPOT WALLET")
print("=" * 50)
bal_spot = ex_spot.fetch_balance()
print(f"USDT: {bal_spot['total']['USDT']:.2f}")

print("\n" + "=" * 50)
print("BYBIT2 FUTURES WALLET")
print("=" * 50)
bal_futures = ex_futures.fetch_balance()
print(f"USDT: {bal_futures['total']['USDT']:.2f}")
print(f"Free: {bal_futures['free']['USDT']:.2f}")
print(f"Used: {bal_futures['used']['USDT']:.2f}")
