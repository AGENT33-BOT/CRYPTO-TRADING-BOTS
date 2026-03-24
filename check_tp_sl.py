import os
from dotenv import load_dotenv
from pybit.unified_trading import HTTP

load_dotenv('.env.bybit')
s = HTTP(api_key=os.getenv('BYBIT_API_KEY'), api_secret=os.getenv('BYBIT_API_SECRET'))

positions = s.get_positions(category='linear', settleCoin='USDT')['result']['list']
for p in positions:
    if float(p.get('size', 0)) > 0:
        print(f"{p['symbol']}: {p['side']} {p['size']} @ {p['avgPrice']}")
        print(f"  TP: {p.get('takeProfit', 'N/A')} | SL: {p.get('stopLoss', 'N/A')}")
