#!/usr/bin/env python3
import ccxt

API_KEY = 'aLz3ySrF9kMZubmqDR'
API_SECRET = '8SlpKyX7vleDu1loJiFePGWfnynJRXZXaD2z'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

print('Fetching positions...')
try:
    positions = exchange.fetch_positions()
    print(f'Total positions returned: {len(positions)}')
    for p in positions:
        size = p.get('contracts') or p.get('size') or 0
        symbol = p.get('symbol')
        side = p.get('side')
        entry = p.get('entryPrice') or p.get('average')
        tp = p.get('takeProfit')
        sl = p.get('stopLoss')
        print(f'  {symbol}: side={side}, size={size}, entry={entry}')
        print(f'    TP: {tp}, SL: {sl}')
        print(f'    Raw info: contracts={p.get("contracts")}, size={p.get("size")}, positionIdx={p.get("positionIdx")}')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
