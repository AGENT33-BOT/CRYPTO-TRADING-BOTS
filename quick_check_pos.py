import ccxt
import os

exchange = ccxt.bybit({
    'apiKey': os.getenv('BYBIT_API_KEY'),
    'secret': os.getenv('BYBIT_SECRET'),
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

positions = exchange.fetch_positions()
open_positions = [p for p in positions if p.get('contracts', 0) != 0]

print(f'Open positions: {len(open_positions)}')
for p in open_positions:
    symbol = p['symbol']
    side = p['side']
    entry = p['entryPrice']
    size = p['contracts']
    tp = p.get('takeProfit', 'Not set')
    sl = p.get('stopLoss', 'Not set')
    unrealized = p.get('unrealizedPnl', 0)
    print(f'{symbol} {side} | Size: {size} | Entry: {entry} | TP: {tp} | SL: {sl} | PnL: ${unrealized:.2f}')
