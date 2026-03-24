import ccxt
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Main Bybit - NEW API
api_key = 'KfmiIdWd16hG18v2O7'
api_secret = 'VTVePZIz2GEqyy6AcvwPVcaRNBRolmXkuWlZ'

# Spot
ex_spot = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
})

# Futures
ex_futures = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

print("=" * 50)
print("MAIN BYBIT ACCOUNT (NEW API)")
print("=" * 50)

# Spot
bal_spot = ex_spot.fetch_balance()
print(f"\nSPOT WALLET:")
for c, a in bal_spot['total'].items():
    if a and a > 0.0001:
        print(f"  {c}: {a:.6f}")

# Futures
bal_futures = ex_futures.fetch_balance()
print(f"\nFUTURES WALLET:")
print(f"  Total: ${bal_futures['total']['USDT']:.2f}")
print(f"  Free: ${bal_futures['free']['USDT']:.2f}")
print(f"  Used: ${bal_futures['used']['USDT']:.2f}")

positions = ex_futures.fetch_positions()
open_pos = [p for p in positions if p.get('contracts', 0) > 0]
print(f"\nOPEN POSITIONS: {len(open_pos)}")
for p in open_pos:
    print(f"  {p['symbol']}: {p['side']} {p['contracts']} @ ${p['entryPrice']} | PnL: ${p['unrealizedPnl']}")
