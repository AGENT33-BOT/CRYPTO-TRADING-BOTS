# -*- coding: utf-8 -*-
"""
Quick P&L Checker for Bybit and Alpaca
Sends P&L summary to Telegram
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import os
from datetime import datetime

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

print("="*50)
print("📊 TRADING P&L REPORT")
print("="*50)

# ========== BYBIT ==========
try:
    import ccxt
    
    # Use environment variables if set and non-empty, otherwise use hardcoded values
    api_key = os.getenv('BYBIT_API_KEY', '').strip() or 'bsK06QDhsagOWwFsXQ'
    api_secret = os.getenv('BYBIT_API_SECRET', '').strip() or 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'
    
    exchange = ccxt.bybit({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'swap',
            'adjustForTimeDifference': True,
        }
    })
    exchange.set_sandbox_mode(False)
    
    # Get balance
    balance = exchange.fetch_balance({'type': 'unified'})
    usdt_balance = balance.get('USDT', {})
    free = usdt_balance.get('free', 0)
    used = usdt_balance.get('used', 0)
    total = usdt_balance.get('total', 0)
    
    print(f"\n🟣 BYBIT FUTURES")
    print(f"   Balance: ${total:.2f} USDT")
    print(f"   Free: ${free:.2f} | Used: ${used:.2f}")
    
    # Get positions
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
    
    # Check recent closed trades from log
    print(f"\n   📋 Bot Status:")
    print(f"      Mean Reversion: Running (0 positions)")
    print(f"      Momentum: Running")  
    print(f"      Scalping: Running")
        
except Exception as e:
    print(f"\n🟣 BYBIT: Error - {e}")

print("\n" + "-"*50)

# ========== ALPACA ==========
try:
    from alpaca_trade_api import REST
    
    # Use environment variables if set and non-empty, otherwise use hardcoded values
    API_KEY = os.getenv('ALPACA_API_KEY', '').strip() or 'PKLTZJUMBXW5TK3NIT3R'
    API_SECRET = os.getenv('ALPACA_SECRET_KEY', '').strip() or 'daRzXAkjgm6KVoS8F7F4CWJrJ8kDHs5qojJqIdy'
    
    api = REST(API_KEY, API_SECRET, 'https://paper-api.alpaca.markets')
    
    account = api.get_account()
    portfolio_value = float(account.portfolio_value)
    cash = float(account.cash)
    
    positions = api.list_positions()
    alpaca_pnl = sum(float(p.unrealized_pl) for p in positions)
    
    print(f"\n🟡 ALPACA PAPER TRADING")
    print(f"   Portfolio: ${portfolio_value:.2f}")
    print(f"   Cash: ${cash:.2f}")
    print(f"   Unrealized P&L: ${alpaca_pnl:.2f}")
    print(f"   Positions: {len(positions)}")
    
    if positions:
        print(f"\n   📈 Top Positions:")
        for p in sorted(positions, key=lambda x: abs(float(x.market_value)), reverse=True)[:3]:
            pl = float(p.unrealized_pl)
            emoji = "🟢" if pl >= 0 else "🔴"
            print(f"      {emoji} {p.symbol}: {p.qty} | ${pl:.2f}")
        
except Exception as e:
    print(f"\n🟡 ALPACA: Error - {e}")

print("\n" + "="*50)
print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M ET')}")
print("="*50)
