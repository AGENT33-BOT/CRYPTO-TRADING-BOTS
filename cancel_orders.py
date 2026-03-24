import ccxt

exchange = ccxt.bybit({
    'apiKey': 'bsK06QDhsagOWwFsXQ',
    'secret': 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa',
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'XRP/USDT:USDT', 
           'ADA/USDT:USDT', 'DOGE/USDT:USDT', 'LINK/USDT:USDT', 'NEAR/USDT:USDT']

all_orders = []
for symbol in symbols:
    try:
        orders = exchange.fetch_open_orders(symbol)
        all_orders.extend(orders)
        if orders:
            print(f"{symbol}: {len(orders)} orders")
    except Exception as e:
        pass

print(f"\nTotal open orders: {len(all_orders)}")

if all_orders:
    print("\nCancelling all orders...")
    for order in all_orders:
        try:
            exchange.cancel_order(order['id'], order['symbol'])
            print(f"  Cancelled: {order['symbol']} {order['side']}")
        except Exception as e:
            print(f"  Error: {e}")
    print(f"\nCancelled {len(all_orders)} orders")
else:
    print("No open orders found")
