import ccxt
import json
import os

exchange = ccxt.bybit({
    'apiKey': os.getenv('BYBIT_API_KEY', ''), 
    'secret': os.getenv('BYBIT_SECRET', ''),
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

try:
    trades = exchange.fetch_my_trades(limit=10)
    for t in trades[:5]:
        print(f"{t['datetime'][:19]} | {t['symbol']} | {t['side'].upper()} | {float(t['amount']):.4f} @ {float(t['price']):.4f}")
except Exception as e:
    print(f'Error: {e}')
