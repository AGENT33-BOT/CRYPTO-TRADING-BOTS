from pybit.unified_trading import HTTP
import os
from dotenv import load_dotenv

load_dotenv('.env.bybit')
sess = HTTP(api_key=os.getenv('BYBIT_API_KEY'), api_secret=os.getenv('BYBIT_API_SECRET'))

print("=== UNIFIED ACCOUNT ===")
try:
    r = sess.get_wallet_balance(accountType='UNIFIED', coin='USDT')
    print(f"Unified USDT: {r}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== SPOT ACCOUNT ===")
try:
    r = sess.get_wallet_balance(accountType='SPOT', coin='USDT')
    print(f"Spot USDT: {r}")
except Exception as e:
    print(f"Error: {e}")
