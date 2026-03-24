import ccxt
import json
from datetime import datetime, timedelta

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

# Check closed positions (order history)
print('=== RECENT ORDERS ===')
try:
    orders = exchange.fetch_closed_orders('BTC/USDT:USDT', since=exchange.parse8601('2026-02-05T11:00:00Z'))
    for order in orders[-10:]:
        print(f"{order['datetime']}: {order['side'].upper()} | {order['amount']} @ {order.get('average', order['price'])} | Status: {order['status']}")
except Exception as e:
    print(f'Error: {e}')

# Check positions more thoroughly
print('\n=== ALL POSITIONS ===')
try:
    positions = exchange.fetch_positions()
    for pos in positions:
        if float(pos.get('contracts', 0)) > 0:
            print(f"{pos['symbol']}: {pos['side'].upper()} | Contracts: {pos['contracts']} | Entry: {pos['entryPrice']} | PnL: {pos.get('unrealizedPnl', 0)}")
except Exception as e:
    print(f'Error: {e}')

# Current BTC price
print('\n=== CURRENT PRICES ===')
for symbol in ['BTC/USDT:USDT', 'ETH/USDT:USDT']:
    try:
        ticker = exchange.fetch_ticker(symbol)
        print(f"{symbol}: ${ticker['last']}")
    except:
        pass
