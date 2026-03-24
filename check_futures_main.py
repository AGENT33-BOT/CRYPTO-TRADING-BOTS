import ccxt
import sys
sys.stdout.reconfigure(encoding='utf-8')

api_key = 'KfmiIdWd16hG18v2O7'
api_secret = 'VTVePZIz2GEqyy6AcvwPVcaRNBRolmXkuWlZ'

# Futures
ex = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

bal = ex.fetch_balance()
print("=" * 50)
print("MAIN BYBIT - FUTURES")
print("=" * 50)
print(f"Total: ${bal['total']['USDT']:.2f}")
print(f"Free:  ${bal['free']['USDT']:.2f}")
print(f"Used:  ${bal['used']['USDT']:.2f}")

positions = ex.fetch_positions()
open_pos = [p for p in positions if p.get('contracts', 0) > 0]
print(f"\nOPEN POSITIONS: {len(open_pos)}")
for p in open_pos:
    print(f"  {p['symbol']}: {p['side']} {p['contracts']} @ ${p['entryPrice']} | PnL: ${p['unrealizedPnl']}")

if not open_pos:
    print("  (none)")
