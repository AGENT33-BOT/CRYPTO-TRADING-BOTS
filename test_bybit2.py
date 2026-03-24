import ccxt

print('Testing Bybit2 connection...')
exchange = ccxt.bybit({
    'apiKey': 'aLz3ySrF9kMZubmqDR',
    'secret': '8SlpKyX7vleDu1loJiFePGWfnynJRXZXaD2z',
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

try:
    balance = exchange.fetch_balance({'type': 'unified'})
    usdt = balance.get('USDT', {})
    total = usdt.get('total', 0)
    print(f'[OK] Connected! Balance: {total:.2f} USDT')
except Exception as e:
    print(f'[ERROR] {e}')
