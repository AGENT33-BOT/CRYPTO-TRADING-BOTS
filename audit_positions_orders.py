import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

symbols = ['XRP/USDT:USDT', 'BCH/USDT:USDT', 'BTC/USDT:USDT', 'ETH/USDT:USDT', 
           'SOL/USDT:USDT', 'ADA/USDT:USDT', 'DOGE/USDT:USDT']

print('=' * 70)
print('POSITION AND ORDER AUDIT')
print('=' * 70)

for symbol in symbols:
    print(f"\n{symbol}:")
    print('-' * 50)
    
    # Check position
    try:
        positions = exchange.fetch_positions([symbol])
        if positions and len(positions) > 0:
            pos = positions[0]
            contracts = float(pos.get('contracts', 0))
            if contracts > 0:
                entry = float(pos.get('entryPrice', 0))
                mark = float(pos.get('markPrice', 0))
                side = pos['side'].upper()
                pnl = float(pos.get('unrealizedPnl', 0))
                print(f"  POSITION: {side} {contracts} | Entry: ${entry:.4f} | Mark: ${mark:.4f} | PnL: ${pnl:+.2f}")
            else:
                print("  POSITION: None")
        else:
            print("  POSITION: None")
    except Exception as e:
        print(f"  POSITION: Error - {e}")
    
    # Check orders
    try:
        orders = exchange.fetch_open_orders(symbol)
        if orders:
            print(f"  ORDERS: {len(orders)} found")
            for i, order in enumerate(orders[:10]):  # Show first 10
                order_type = order['type']
                side = order['side']
                price = order.get('price', 'MARKET')
                amount = order.get('amount', 0)
                print(f"    {i+1}. {order_type.upper()} {side.upper()} | Qty: {amount} | Price: {price}")
            if len(orders) > 10:
                print(f"    ... and {len(orders) - 10} more orders")
        else:
            print("  ORDERS: None")
    except Exception as e:
        print(f"  ORDERS: Error - {e}")

print('\n' + '=' * 70)
