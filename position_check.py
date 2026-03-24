#!/usr/bin/env python3
"""Quick position TP/SL check using ccxt"""
import os
import sys
sys.stdout.reconfigure(encoding='utf-8') if sys.platform == 'win32' else None

os.chdir(r'C:\Users\digim\clawd\crypto_trader')

from dotenv import load_dotenv
load_dotenv()

import ccxt

api_key = os.getenv('BYBIT_API_KEY')
secret = os.getenv('BYBIT_API_SECRET')

exchange = ccxt.bybit({
    'apiKey': api_key,
    'secret': secret,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

positions = exchange.fetch_positions()

print("=" * 60)
print("📊 CURRENT POSITIONS - TP/SL CHECK")
print("=" * 60)

for p in positions:
    size = float(p.get('contracts', 0))
    if size != 0:
        symbol = p['symbol']
        entry = float(p.get('entryPrice', 0))
        tp = float(p.get('takeProfitPrice', 0) or p.get('takeProfit', 0))
        sl = float(p.get('stopLossPrice', 0) or p.get('stopLoss', 0))
        pnl = float(p.get('unrealizedPnl', 0))
        side = p.get('side', 'unknown')
        
        tp_status = "✅ SET" if tp != 0 else "❌ MISSING"
        sl_status = "✅ SET" if sl != 0 else "❌ MISSING"
        
        print(f"\n🔹 {symbol} ({side.upper()})")
        print(f"   Size: {size} | Entry: ${entry:.4f}")
        print(f"   P&L: ${pnl:.2f}")
        print(f"   TP: ${tp:.4f} ({tp_status})")
        print(f"   SL: ${sl:.4f} ({sl_status})")

print("\n" + "=" * 60)
