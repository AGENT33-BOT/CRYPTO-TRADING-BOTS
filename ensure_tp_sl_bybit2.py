#!/usr/bin/env python3
"""Bybit2 TP/SL Guardian - Checks secondary Bybit account"""
import os
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import ccxt
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / '.env.bybit2'
load_dotenv(ENV_PATH)

API_KEY = os.getenv('BYBIT_API_KEY')
API_SECRET = os.getenv('BYBIT_API_SECRET')
USE_TESTNET = False

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def connect_bybit():
    exchange = ccxt.bybit({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })
    return exchange

def get_open_positions(exchange):
    try:
        response = exchange.private_get_v5_position_list({
            'category': 'linear', 
            'settleCoin': 'USDT', 
            'limit': 50
        })
        if str(response.get('retCode')) != '0':
            log(f"⚠️ API warning: {response.get('retMsg')}")
            return []
        
        positions = response.get('result', {}).get('list', [])
        open_positions = []
        for pos in positions:
            size = float(pos.get('size', 0) or 0)
            if size != 0:
                open_positions.append({
                    'symbol': pos.get('symbol', ''),
                    'side': 'long' if pos.get('side') == 'Buy' else 'short',
                    'entryPrice': float(pos.get('avgPrice', 0) or 0),
                    'contracts': size,
                    'takeProfit': float(pos.get('takeProfit', 0) or 0),
                    'stopLoss': float(pos.get('stopLoss', 0) or 0),
                })
        return open_positions
    except Exception as e:
        log(f"❌ Error: {e}")
        return []

def check_tp_sl(position):
    tp = position.get('takeProfit', 0)
    sl = position.get('stopLoss', 0)
    return float(tp) > 0, float(sl) > 0

log("=" * 60)
log("🔒 BYBIT2 TP/SL GUARDIAN (Secondary Account)")
log("=" * 60)

try:
    exchange = connect_bybit()
    log("✅ Connected to Bybit2 API")
except Exception as e:
    log(f"❌ Failed to connect: {e}")
    sys.exit(1)

positions = get_open_positions(exchange)

if not positions:
    log("📭 No open positions found")
    log("=" * 60)
else:
    log(f"📊 Found {len(positions)} open position(s)")
    log("")
    
    for pos in positions:
        symbol = pos['symbol']
        side = pos.get('side', 'unknown').upper()
        entry = float(pos.get('entryPrice', 0))
        size = float(pos.get('contracts', 0))
        has_tp, has_sl = check_tp_sl(pos)
        
        log(f"📈 {symbol} {side}")
        log(f"   Entry: {entry:.4f} | Size: {size}")
        log(f"   TP: {'✅ Set' if has_tp else '❌ MISSING'}")
        log(f"   SL: {'✅ Set' if has_sl else '❌ MISSING'}")
        log(f"   {'✓ Already protected' if (has_tp and has_sl) else '🚨 NEEDS PROTECTION'}")
        log("")
    
    log("=" * 60)
    log("✅ All positions checked")
    log("=" * 60)
