#!/usr/bin/env python3
"""Close NEAR position immediately - violates ETH/SOL-only policy"""
import sys
import os
sys.path.insert(0, r'C:\Users\digim\clawd\crypto_trader')
os.chdir(r'C:\Users\digim\clawd\crypto_trader')

from dotenv import load_dotenv
load_dotenv()

from pybit.unified_trading import HTTP

session = HTTP(
    api_key=os.getenv('BYBIT_API_KEY'),
    api_secret=os.getenv('BYBIT_SECRET'),
    testnet=False
)

try:
    result = session.place_order(
        category='linear',
        symbol='NEARUSDT',
        side='Sell',
        orderType='Market',
        qty=96,
        reduceOnly=True
    )
    print("CLOSED NEARUSDT LONG 96 @ market - Policy violation fixed")
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")
