#!/usr/bin/env python3
"""Quick TP/SL check and fix using pybit"""
from pybit.unified_trading import HTTP
import os

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

session = HTTP(testnet=False, api_key=API_KEY, api_secret=API_SECRET)

# Get all positions
try:
    result = session.get_positions(category='linear', settleCoin='USDT')
    positions = result.get('result', {}).get('list', [])
    
    print('=' * 60)
    print('POSITIONS TP/SL STATUS CHECK')
    print('=' * 60)
    
    needs_fix = []
    
    for pos in positions:
        size = float(pos.get('size', 0))
        if size == 0:
            continue
            
        symbol = pos.get('symbol', 'N/A')
        side = pos.get('side', 'N/A')
        entry = float(pos.get('avgPrice', 0))
        mark = float(pos.get('markPrice', 0))
        pnl = float(pos.get('unrealisedPnl', 0))
        
        tp = pos.get('takeProfit', '0')
        sl = pos.get('stopLoss', '0')
        has_tp = tp and float(tp) > 0
        has_sl = sl and float(sl) > 0
        
        status = "OK" if (has_tp and has_sl) else "NEEDS TP/SL"
        
        print(f"\n{symbol} {side}")
        print(f"  Size: {size} | Entry: ${entry:.4f} | Mark: ${mark:.4f}")
        print(f"  PnL: ${pnl:+.2f}")
        print(f"  TP: {tp if has_tp else 'NOT SET'}")
        print(f"  SL: {sl if has_sl else 'NOT SET'}")
        print(f"  Status: {status}")
        
        if not (has_tp and has_sl):
            needs_fix.append({
                'symbol': symbol,
                'side': side,
                'size': size,
                'entry': entry
            })
    
    print(f"\n{'=' * 60}")
    
    if needs_fix:
        print(f"⚠️  {len(needs_fix)} position(s) need TP/SL:")
        for p in needs_fix:
            print(f"   - {p['symbol']} {p['side']}")
    else:
        print("✅ All positions have TP/SL set!")
    
    print('=' * 60)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
