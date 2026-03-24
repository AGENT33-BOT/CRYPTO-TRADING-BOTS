#!/usr/bin/env python3
"""Close XRP SHORT position - wrong direction for LONG bias"""
import os
import sys
import ccxt
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / '.env.bybit'
load_dotenv(ENV_PATH)

API_KEY = os.getenv('BYBIT_API_KEY')
API_SECRET = os.getenv('BYBIT_API_SECRET')

def connect_bybit():
    exchange = ccxt.bybit({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })
    return exchange

def close_xrp_short():
    exchange = connect_bybit()
    symbol = 'XRP/USDT:USDT'
    
    try:
        # Get position
        positions = exchange.fetch_positions([symbol])
        for pos in positions:
            size = float(pos.get('contracts', 0) or pos.get('size', 0) or 0)
            side = pos.get('side', '').lower()
            
            if size > 0 and side == 'short':
                print(f"Closing XRP SHORT: {size} units")
                # Close by creating opposite order
                order = exchange.create_market_buy_order(symbol, size)
                print(f"✅ XRP SHORT closed: {order['id']}")
                return True
        
        print("No XRP SHORT position found")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    close_xrp_short()
