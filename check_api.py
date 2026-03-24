import os
import json
from dotenv import load_dotenv
load_dotenv()

from pybit import HTTP

h = HTTP('https://api.bybit.com', api_key=os.getenv('BYBIT_API_KEY'), api_secret=os.getenv('BYBIT_API_SECRET'))

# Get wallet balance
try:
    w = h.get_wallet_balance(accountType='UNIFIED')
    print("=== WALLET ===")
    print(json.dumps(w, indent=2))
except Exception as e:
    print(f"Wallet error: {e}")

# Get positions
try:
    p = h.get_positions(category='linear', limit=20)
    print("\n=== POSITIONS ===")
    print(json.dumps(p, indent=2))
except Exception as e:
    print(f"Positions error: {e}")
