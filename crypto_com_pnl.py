# -*- coding: utf-8 -*-
"""
Quick P&L Checker for Crypto.com
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import os
from datetime import datetime

print("="*50)
print("📊 CRYPTO.COM P&L REPORT")
print("="*50)

try:
    import ccxt
    
    # Load credentials
    creds_file = 'crypto_com_credentials.json'
    api_key = os.environ.get('CRYPTOCOM_API_KEY', '')
    api_secret = os.environ.get('CRYPTOCOM_API_SECRET', '')
    
    if not api_key and os.path.exists(creds_file):
        with open(creds_file, 'r') as f:
            creds = json.load(f)
            api_key = creds.get('api_key', '')
            api_secret = creds.get('api_secret', '')
    
    if not api_key or not api_secret:
        print("\n🟡 CRYPTO.COM: API credentials not configured")
        print("   Set CRYPTOCOM_API_KEY and CRYPTOCOM_API_SECRET")
        print("   Or create crypto_com_credentials.json")
    else:
        exchange = ccxt.cryptocom({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',
            }
        })
        
        # Load markets
        exchange.load_markets()
        
        # Get balance
        balance = exchange.fetch_balance()
        usd_balance = balance.get('USD', {})
        free = usd_balance.get('free', 0)
        used = usd_balance.get('used', 0)
        total = usd_balance.get('total', 0)
        
        print(f"\n🟣 CRYPTO.COM FUTURES")
        print(f"   Balance: ${total:.2f} USD")
        print(f"   Free: ${free:.2f} | Used: ${used:.2f}")
        
        # Get positions
        try:
            positions = exchange.fetch_positions()
            
            open_positions = []
            total_unrealized = 0
            
            for pos in positions:
                size = float(pos.get('contracts', 0) or 0)
                if size != 0:
                    symbol = pos.get('symbol', 'Unknown')
                    side = pos.get('side', 'Unknown')
                    entry = float(pos.get('entryPrice', 0) or 0)
                    mark = float(pos.get('markPrice', 0) or 0)
                    unrealized = float(pos.get('unrealizedPnl', 0) or 0)
                    total_unrealized += unrealized
                    
                    emoji = "🟢" if side == 'long' else "🔴"
                    open_positions.append(f"   {emoji} {symbol} {side.upper()}: {size} @ ${entry:.4f} | P&L: ${unrealized:.2f}")
            
            if open_positions:
                print(f"\n   📈 Open Positions ({len(open_positions)}):")
                for p in open_positions:
                    print(p)
                print(f"\n   💵 Total Unrealized P&L: ${total_unrealized:.2f}")
            else:
                print("\n   📭 No open positions")
        except Exception as e:
            print(f"\n   📭 Positions: Could not fetch - {e}")
        
        print(f"\n   📋 Agent Status:")
        print(f"      Strategy: RSI + Bollinger Bands")
        print(f"      Timeframe: 1m")
        print(f"      Leverage: 3x")
        
except Exception as e:
    print(f"\n🟣 CRYPTO.COM: Error - {e}")

print("\n" + "="*50)
print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M ET')}")
print("="*50)
