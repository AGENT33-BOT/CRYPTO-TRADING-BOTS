import ccxt
import os

exchange = ccxt.bybit({
    'apiKey': os.getenv('BYBIT2_API_KEY'),
    'secret': os.getenv('BYBIT2_API_SECRET'),
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})
balance = exchange.fetch_balance()
usdt = balance.get('USDT', {})
print(f"Bybit2 Balance: ${usdt.get('free', 0):.2f} free / ${usdt.get('total', 0):.2f} total")
