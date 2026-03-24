import ccxt
import os

# Bybit credentials
api_key = 'aLz3ySrF9kMZubmqDR'
api_secret = '8SlpKyX7vleDu1loJiFePGWfnynJRXZXaD2z'

exchange = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
})

# Get positions
positions = exchange.fetch_positions()
print("All positions:")
for p in positions:
    if p['symbol'] and float(p.get('contracts', 0) or 0) != 0:
        print(f"  {p['symbol']}: side={p['side']}, contracts={p.get('contracts')}, unrealizedPNL={p.get('unrealizedPnl')}")

# Find and close SOL SHORT
for p in positions:
    if 'SOL' in p['symbol'] and p['side'] == 'short' and float(p.get('contracts', 0) or 0) > 0:
        print(f"\nClosing SHORT: {p['symbol']}")
        try:
            # Close the short by going long
            close_order = exchange.create_order(
                symbol=p['symbol'],
                type='market',
                side='buy',
                amount=float(p['contracts']),
                params={'reduceOnly': True}
            )
            print(f"SUCCESS: {close_order}")
        except Exception as e:
            print(f"Error: {e}")
