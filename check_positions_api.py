import ccxt

BYBIT_API_KEY = 'bsK06QDhsagOWwFsXQ'
BYBIT_API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': BYBIT_API_KEY,
    'secret': BYBIT_API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})
exchange.load_markets()

print('=== Direct API call: v5_position/list ===')
try:
    result = exchange.private_get_v5_position_list({'category': 'linear', 'settleCoin': 'USDT'})
    positions = result.get('result', {}).get('list', [])
    print(f"Count: {len(positions)}")
    for p in positions:
        size = float(p.get('size') or 0)
        if size != 0:
            tp = p.get('takeProfit', 'NONE')
            sl = p.get('stopLoss', 'NONE')
            entry = p.get('avgPrice', 'N/A')
            print(f"  {p['symbol']}: {p['side']} {size} contracts | Entry: {entry} | TP: {tp} | SL: {sl}")
    if not positions:
        print("  No positions found")
except Exception as e:
    print(f'Error: {e}')
