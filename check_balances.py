import os
from dotenv import load_dotenv
from pybit.unified_trading import HTTP

# Check Main Account (.env.bybit)
load_dotenv('.env.bybit')
api = HTTP(api_key=os.getenv('BYBIT_API_KEY'), api_secret=os.getenv('BYBIT_API_SECRET'), testnet=False)
result = api.get_wallet_balance(accountType='UNIFIED', coin='USDT')
if result['retCode'] == 0:
    bal = result['result']['list'][0]['coin'][0]
    print(f'Main Account (.env.bybit): {bal["equity"]} USDT')
else:
    print(f'Main Error: {result}')

# Check Bybit2
load_dotenv('.env.bybit2')
api2 = HTTP(api_key=os.getenv('BYBIT_API_KEY'), api_secret=os.getenv('BYBIT_API_SECRET'), testnet=False)
result2 = api2.get_wallet_balance(accountType='UNIFIED', coin='USDT')
if result2['retCode'] == 0:
    bal2 = result2['result']['list'][0]['coin'][0]
    print(f'Bybit2 Account: {bal2["equity"]} USDT')
else:
    print(f'Bybit2 Error: {result2}')

# Check old .env
load_dotenv('.env')
api3 = HTTP(api_key=os.getenv('BYBIT_API_KEY'), api_secret=os.getenv('BYBIT_SECRET'), testnet=False)
result3 = api3.get_wallet_balance(accountType='UNIFIED', coin='USDT')
if result3['retCode'] == 0:
    bal3 = result3['result']['list'][0]['coin'][0]
    print(f'Old .env main: {bal3["equity"]} USDT')
else:
    print(f'.env Error: {result3}')
