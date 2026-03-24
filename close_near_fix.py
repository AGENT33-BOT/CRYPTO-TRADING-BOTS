from pybit.unified_trading import HTTP
import config

session = HTTP(api_key=config.API_KEY, api_secret=config.API_SECRET, testnet=config.TESTNET)
positions = session.get_positions(category='linear', settleCoin='USDT')['result']['list']
for p in positions:
    size = float(p['size'])
    if size > 0:
        print(f"Symbol: {p['symbol']}, Side: {p['side']}, Size: {size}")
        if p['symbol'] == 'NEARUSDT':
            close_side = 'Sell' if p['side'] == 'Buy' else 'Buy'
            order = session.place_order(category='linear', symbol='NEARUSDT', side=close_side, orderType='Market', qty=size, reduceOnly=True, timeInForce='GTC')
            print(f'Closed NEAR: {order}')
