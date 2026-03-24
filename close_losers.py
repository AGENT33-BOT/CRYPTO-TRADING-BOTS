from pybit.unified_trading import HTTP
import os

session = HTTP(testnet=False, api_key=os.getenv('BYBIT_API_KEY'), api_secret=os.getenv('BYBIT_API_SECRET'))

# Get current positions
resp = session.get_positions(category='linear', settleCoin='USDT')

print("CLOSING LOSER POSITIONS")
print("=" * 50)

losers = ['LINK', 'ADA', 'DOT', 'AVAX']  # Symbols to close

for pos in resp['result']['list']:
    symbol = pos['symbol']
    size = float(pos['size'])
    
    if size > 0:
        base_symbol = symbol.split('/')[0]
        
        if base_symbol in losers:
            side = 'Sell' if pos['side'] == 'Buy' else 'Buy'
            print(f"Closing {symbol} {pos['side']} position ({size} units)...")
            
            try:
                resp = session.place_order(
                    category='linear',
                    symbol=symbol,
                    side=side,
                    orderType='Market',
                    qty=str(size),
                    reduceOnly=True
                )
                print(f"  ✓ Closed - Order ID: {resp['result']['orderId']}")
            except Exception as e:
                print(f"  ✗ Error: {e}")

print("\nDone!")
