# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import ccxt

api_key = 'bsK06QDhsagOWwFsXQ'
api_secret = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

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

positions = exchange.fetch_positions()
print("POSITION TP/SL STATUS:\n")

for p in positions:
    size = float(p.get('contracts', 0) or p.get('size', 0) or 0)
    if size != 0:
        symbol = p.get('symbol', 'Unknown')
        side = p.get('side', 'Unknown')
        entry = float(p.get('entryPrice', 0) or p.get('average', 0) or 0)
        tp = p.get('takeProfit', 0)
        sl = p.get('stopLoss', 0)
        tp_price = float(tp) if tp else 0
        sl_price = float(sl) if sl else 0
        
        tp_status = "SET" if tp_price > 0 else "MISSING"
        sl_status = "SET" if sl_price > 0 else "MISSING"
        
        print(f"{symbol} ({side}):")
        print(f"  Entry: ${entry:.4f}")
        print(f"  TP: ${tp_price:.4f} [{tp_status}]")
        print(f"  SL: ${sl_price:.4f} [{sl_status}]")
        print()
