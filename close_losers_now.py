"""
Close losing positions - Emergency fix
"""

import ccxt
import os

# Load API credentials
api_key = os.environ.get('BYBIT_API_KEY', '')
api_secret = os.environ.get('BYBIT_API_SECRET', '')

exchange = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'swap',
    }
})

# Positions to CLOSE (losers)
close_symbols = [
    'BTC/USDT:USDT',
    'AVAX/USDT:USDT', 
    'ARB/USDT:USDT',
    'DOGE/USDT:USDT',
    'XRP/USDT:USDT',
    'LINK/USDT:USDT'
]

print("="*60)
print("CLOSING LOSING POSITIONS - KEEPING ETH & NEAR ONLY")
print("="*60)

for symbol in close_symbols:
    try:
        # Check if position exists
        positions = exchange.fetch_positions([symbol])
        for pos in positions:
            size = float(pos.get('contracts', 0))
            if size != 0:
                side = 'sell' if pos['side'] == 'long' else 'buy'
                print(f"Closing {symbol}: {size} contracts ({pos['side']})")
                
                # Close position
                order = exchange.create_order(
                    symbol=symbol,
                    type='market',
                    side=side,
                    amount=abs(size),
                    params={'reduceOnly': True}
                )
                print(f"  ✓ Closed - Order ID: {order['id']}")
    except Exception as e:
        print(f"  ✗ Error closing {symbol}: {e}")

print("="*60)
print("DONE - Only ETH and NEAR positions remain")
print("="*60)
