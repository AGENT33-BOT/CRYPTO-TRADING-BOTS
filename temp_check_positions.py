from pybit.unified_trading import HTTP
import os
from dotenv import load_dotenv

load_dotenv()
session = HTTP(testnet=False, api_key=os.getenv('BYBIT_API_KEY'), api_secret=os.getenv('BYBIT_SECRET'))
positions = session.get_positions(category='linear', settleCoin='USDT')['result']['list']
for p in positions:
    if float(p['size']) > 0:
        print(f"{p['symbol']}: Entry={p['avgPrice']}, Size={p['size']}, TP={p.get('takeProfit','N/A')}, SL={p.get('stopLoss','N/A')}, TPSLMode={p.get('tpslMode','N/A')}")
