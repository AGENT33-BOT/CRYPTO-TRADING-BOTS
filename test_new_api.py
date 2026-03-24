import ccxt
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Main Bybit - NEW API
api_key = 'KfmiIdWd16hG18v2O7'
api_secret = 'VTVePZIz2GEqyy6AcvwPVcaRNBRolmXkuWlZ'

ex = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

# Test with balance check
bal = ex.fetch_balance()
print("API Working!")
print(f"Balance: ${bal['total']['USDT']:.2f} USDT")
print(f"Free: ${bal['free']['USDT']:.2f}")
print(f"Used: ${bal['used']['USDT']:.2f}")

# Get positions
positions = ex.fetch_positions()
print(f"\nPositions: {len([p for p in positions if p.get('contracts', 0) > 0])}")
for p in positions:
    if p.get('contracts', 0) > 0:
        print(f"  {p['symbol']}: {p['side']} {p['contracts']} @ ${p['entryPrice']} | PnL: ${p['unrealizedPnl']}")
