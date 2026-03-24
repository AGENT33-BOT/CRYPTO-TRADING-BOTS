import ccxt
import sys
sys.stdout.reconfigure(encoding='utf-8')

api_key = 'KfmiIdWd16hG18v2O7'
api_secret = 'VTVePZIz2GEqyy6AcvwPVcaRNBRolmXkuWlZ'

# Spot
ex_spot = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
})

print("=" * 50)
print("MAIN BYBIT - SPOT WALLET")
print("=" * 50)

bal = ex_spot.fetch_balance()
print(f"\nSPOT WALLET - ALL ASSETS:")
has_crypto = False
for c, a in bal['total'].items():
    if a and a > 0.00001:
        free = bal['free'].get(c, 0)
        print(f"  {c}: {a:.8f} (Free: {free:.8f})")
        if c != 'USDT' and a > 0.00001:
            has_crypto = True

print(f"\nUSDT only: ${bal['total']['USDT']:.2f}")

if has_crypto:
    print("\n⚠️  CRYPTO HOLDINGS FOUND - SELLING...")
else:
    print("\n✅ SPOT WALLET: USDT ONLY - NOTHING TO SELL")
