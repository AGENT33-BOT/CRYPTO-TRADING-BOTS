import ccxt
import os
from dotenv import load_dotenv
load_dotenv()

exchange = ccxt.bybit({
    'apiKey': os.getenv('BYBIT_API_KEY'),
    'secret': os.getenv('BYBIT_API_SECRET'),
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

# Test connection
print('Fetching balance...')
balance = exchange.fetch_balance()
print(f"USDT Balance: {balance.get('USDT', {}).get('free', 'N/A')}")

print('\nFetching positions with different methods...')

# Method 1: fetch_positions
positions1 = exchange.fetch_positions()
print(f'fetch_positions(): {len(positions1)} positions')

# Method 2: fetch_positions with symbols=None explicitly
positions2 = exchange.fetch_positions(None)
print(f'fetch_positions(None): {len(positions2)} positions')

# Method 3: Try linear category
print('\nTrying fetch_positions with params...')
try:
    positions3 = exchange.fetch_positions(None, {'category': 'linear'})
    print(f"fetch_positions(params): {len(positions3)} positions")
    if positions3:
        for p in positions3[:2]:
            print(f"  - {p.get('symbol')}: size={p.get('contracts') or p.get('size')}, side={p.get('side')}")
except Exception as e:
    print(f'Error: {e}')

print('\nDone!')
