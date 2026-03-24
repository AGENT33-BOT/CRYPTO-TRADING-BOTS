import sys
sys.path.insert(0, '.')
from bybit_futures_trader import BybitFuturesTrader
import os
from dotenv import load_dotenv
load_dotenv('.env.bybit')
trader = BybitFuturesTrader(
    api_key=os.getenv('BYBIT_API_KEY'),
    api_secret=os.getenv('BYBIT_API_SECRET'),
    testnet=False
)
result = trader.close_position('ADAUSDT')
print(f'Closed ADA: {result}')