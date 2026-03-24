import os
from pathlib import Path
from dotenv import load_dotenv
from pybit.unified_trading import HTTP

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / '.env.bybit'
load_dotenv(ENV_PATH)
API_KEY = os.getenv('BYBIT_API_KEY')
API_SECRET = os.getenv('BYBIT_API_SECRET')
session = HTTP(api_key=API_KEY, api_secret=API_SECRET, testnet=False)

wallet = session.get_wallet_balance(accountType='UNIFIED', coin='USDT')
balance_info = wallet['result']['list'][0]['coin'][0]
print('USDT Balance:', balance_info.get('equity'))
print('Available:', balance_info.get('availableToWithdraw'))

positions = session.get_positions(category='linear', settleCoin='USDT')
open_positions = [p for p in positions['result']['list'] if float(p.get('size', 0)) > 0]
print('Open Positions:', len(open_positions))

for p in open_positions:
    print(f"  {p['symbol']}: {p['side']} {p['size']} @ {p['avgPrice']} | PnL: {p['unrealisedPnl']}")
