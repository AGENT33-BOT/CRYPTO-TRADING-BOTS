import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 
           'XRP/USDT:USDT', 'ADA/USDT:USDT', 'DOGE/USDT:USDT',
           'LINK/USDT:USDT', 'NEAR/USDT:USDT', 'AVAX/USDT:USDT',
           'MATIC/USDT:USDT', 'DOT/USDT:USDT', 'LTC/USDT:USDT',
           'BCH/USDT:USDT', 'ETC/USDT:USDT', 'FIL/USDT:USDT']

total_cancelled = 0

for symbol in symbols:
    try:
        orders = exchange.fetch_open_orders(symbol)
        if orders:
            print(f"{symbol}: {len(orders)} orders to cancel")
            for order in orders:
                exchange.cancel_order(order['id'], symbol)
                print(f"  Cancelled: {order['side']} {order['type']} @ {order.get('price', 'N/A')}")
                total_cancelled += 1
    except Exception as e:
        print(f"{symbol}: {e}")

print(f"\nTotal cancelled: {total_cancelled}")
