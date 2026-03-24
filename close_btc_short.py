import ccxt

api_key = 'KfmiIdWd16hG18v2O7'
api_secret = 'VTVePZIz2GEqyy6AcvwPVcaRNBRolmXkuWlZ'

ex = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

print("Finding BTC SHORT positions...")

positions = ex.fetch_positions()
for p in positions:
    if p.get('contracts', 0) > 0 and 'BTC' in p['symbol'] and p['side'].lower() == 'short':
        print(f"Found: {p['symbol']} {p['side']} {p['contracts']} @ ${p['entryPrice']}")
        
        # Close the position
        try:
            order = ex.create_order(
                symbol=p['symbol'],
                type='market',
                side='buy',  # Close short = buy
                amount=p['contracts']
            )
            print(f"✅ CLOSED: BTC/USDT SHORT")
            print(f"   PnL: ${p['unrealizedPnl']}")
        except Exception as e:
            print(f"❌ Error: {e}")
