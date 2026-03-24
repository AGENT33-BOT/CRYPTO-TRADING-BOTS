from pybit.unified_trading import HTTP
import config

session = HTTP(api_key=config.API_KEY, api_secret=config.API_SECRET, testnet=config.TESTNET)
pos = session.get_positions(category='linear', settleCoin='USDT')

print("=== OPEN POSITIONS ===")
for p in pos['result']['list']:
    if float(p['size']) > 0:
        print(f"Symbol: {p['symbol']}, Side: {p['side']}, Size: {p['size']}, Entry: {p['avgPrice']}")
        
# Try to close NEAR
for p in pos['result']['list']:
    if float(p['size']) > 0 and 'NEAR' in p['symbol']:
        print(f"\n>>> Closing {p['symbol']} {p['side']} {p['size']}")
        side = 'Sell' if p['side'] == 'Buy' else 'Buy'
        try:
            order = session.place_order(
                category='linear',
                symbol=p['symbol'],
                side=side,
                orderType='Market',
                qty=p['size'],
                reduceOnly=True
            )
            print(f"Result: {order}")
        except Exception as e:
            print(f"Error: {e}")
