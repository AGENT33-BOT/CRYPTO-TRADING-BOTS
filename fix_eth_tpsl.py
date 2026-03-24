#!/usr/bin/env python3
from pybit.unified_trading import HTTP
import os
from dotenv import load_dotenv

load_dotenv()
session = HTTP(api_key=os.getenv('BYBIT_API_KEY'), api_secret=os.getenv('BYBIT_SECRET'), testnet=False)

SYMBOL = "ETHUSDT"
ENTRY = 1978.585
SIZE = 0.02

# Set TP at +2.5% and SL at -1.5%
TP = round(ENTRY * 1.025, 2)
SL = round(ENTRY * 0.985, 2)

print(f"Setting TP/SL for {SYMBOL}:")
print(f"  Entry: ${ENTRY}")
print(f"  TP: ${TP} (+2.5%)")
print(f"  SL: ${SL} (-1.5%)")

result = session.set_trading_stop(
    category="linear",
    symbol=SYMBOL,
    takeProfit=str(TP),
    stopLoss=str(SL),
    positionIdx=0
)

print(f"\nResult: {result}")
