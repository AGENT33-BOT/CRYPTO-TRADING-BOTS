#!/usr/bin/env python3
"""Set TP/SL for positions that don't have them"""
from pybit.unified_trading import HTTP

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

session = HTTP(testnet=False, api_key=API_KEY, api_secret=API_SECRET)

# 2% SL / 3% TP config
SL_PCT = 0.02
TP_PCT = 0.03

symbols_to_fix = [
    {'symbol': 'SOLUSDT', 'side': 'Buy', 'size': 0.1, 'entry': 81.62},
    {'symbol': 'DOGEUSDT', 'side': 'Buy', 'size': 267.0, 'entry': 0.0936},
    {'symbol': 'ETHUSDT', 'side': 'Buy', 'size': 0.01, 'entry': 1981.91}
]

print('=' * 60)
print('SETTING TP/SL FOR POSITIONS')
print('=' * 60)

for pos in symbols_to_fix:
    symbol = pos['symbol']
    side = pos['side']
    size = pos['size']
    entry = pos['entry']
    
    print(f"\n{symbol} {side}")
    print(f"  Entry: ${entry}")
    print(f"  Size: {size}")
    
    if side == 'Buy':  # LONG
        tp = entry * (1 + TP_PCT)
        sl = entry * (1 - SL_PCT)
    else:  # SHORT
        tp = entry * (1 - TP_PCT)
        sl = entry * (1 + SL_PCT)
    
    print(f"  TP: ${tp:.4f} ({TP_PCT*100:.0f}%)")
    print(f"  SL: ${sl:.4f} ({SL_PCT*100:.0f}%)")
    
    # Set TP/SL using trading stop
    try:
        result = session.set_trading_stop(
            category='linear',
            symbol=symbol,
            takeProfit=str(round(tp, 4)),
            stopLoss=str(round(sl, 4)),
            tpTriggerBy='MarkPrice',
            slTriggerBy='MarkPrice',
            tpslMode='Full'
        )
        print(f"  [OK] TP/SL set successfully")
        print(f"  Result: {result.get('retMsg', 'OK')}")
    except Exception as e:
        print(f"  [ERROR] {e}")

print(f"\n{'=' * 60}")
print('DONE')
print('=' * 60)
