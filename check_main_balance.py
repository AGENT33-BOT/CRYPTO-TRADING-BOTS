import os
import sys
from pybit import HTTP

# Check main Bybit account
api_key = os.environ.get('BYBIT_API_KEY')
api_secret = os.environ.get('BYBIT_API_SECRET')

if api_key and api_secret:
    h = HTTP(testnet=False, api_key=api_key, api_secret=api_secret)
    result = h.get_wallet_balance()
    print("MAIN BYBIT ACCOUNT:")
    print(result)
else:
    print("No main BYBIT_API_KEY found")
