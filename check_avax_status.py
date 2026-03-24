import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

# Check AVAX specifically
symbol = 'AVAX/USDT:USDT'
print(f'=== {symbol} STATUS ===')

try:
    # Get position
    positions = exchange.fetch_positions([symbol])
    if positions and len(positions) > 0:
        pos = positions[0]
        contracts = float(pos.get('contracts', 0))
        if contracts > 0:
            print(f"Side: {pos['side'].upper()}")
            print(f"Entry: ${pos['entryPrice']}")
            print(f"Mark: ${pos['markPrice']}")
            print(f"Size: {contracts}")
            print(f"PnL: ${float(pos.get('unrealizedPnl', 0)):+.2f}")
            print(f"Stop Loss: {pos.get('stopLossPrice', 'NOT SET')}")
            print(f"Take Profit: {pos.get('takeProfitPrice', 'NOT SET')}")
        else:
            print("No position found")
    else:
        print("No position found")
        
    # Check open orders
    print(f'\n=== {symbol} ORDERS ===')
    orders = exchange.fetch_open_orders(symbol)
    if orders:
        for order in orders:
            print(f"  {order['type'].upper()} | {order['side'].upper()} | {order['amount']} @ {order['price']}")
    else:
        print("  No open orders")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
