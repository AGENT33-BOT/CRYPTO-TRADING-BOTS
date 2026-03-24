#!/usr/bin/env python3
import ccxt
import os
from dotenv import load_dotenv
load_dotenv()

exchange = ccxt.bybit({
    'apiKey': 'KfmiIdWd16hG18v2O7',
    'secret': 'VTVePZIz2GEqyy6AcvwPVcaRNBRolmXkuWlZ',
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

positions = exchange.fetch_positions()
print("=== POSITION DETAILS ===")
for pos in positions:
    if float(pos.get('contracts', 0)) != 0:
        print(f"Symbol: {pos['symbol']}")
        print(f"  Side: {pos['side']}")
        print(f"  Size: {pos['contracts']}")
        print(f"  Entry: {pos['entryPrice']}")
        print(f"  TP Price: {pos.get('takeProfitPrice', 'N/A')}")
        print(f"  SL Price: {pos.get('stopLossPrice', 'N/A')}")
        print(f"  Raw TP: {pos.get('takeProfit', 'N/A')}")
        print(f"  Raw SL: {pos.get('stopLoss', 'N/A')}")
        print(f"  Info: {pos.get('info', {})}")
        print()
