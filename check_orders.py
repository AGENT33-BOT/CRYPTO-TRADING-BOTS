import os
from pathlib import Path
from dotenv import load_dotenv
from pybit.unified_trading import HTTP

load_dotenv(Path('.env.bybit'))
API_KEY = os.getenv('BYBIT_API_KEY')
API_SECRET = os.getenv('BYBIT_API_SECRET')

session = HTTP(api_key=API_KEY, api_secret=API_SECRET)

# Check open orders for USDT pairs
orders = session.get_open_orders(category='linear', settleCoin='USDT')
print("Open Orders:", orders)

# Check wallet breakdown
wallet = session.get_wallet_balance(accountType='UNIFIED', coin='USDT')
print("\nWallet:", wallet)
