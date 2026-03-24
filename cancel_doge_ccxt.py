import ccxt

# Bybit credentials
api_key = 'bsK06QDhsagOWwFsXQ'
api_secret = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
})

# Get open orders for DOGEUSDT (linear futures)
try:
    orders = exchange.fetch_open_orders('DOGE/USDT:USDT')
    print(f'Open DOGE orders: {len(orders)}')

    for o in orders:
        print(f"  {o['id']} | {o['side']} | {o['type']} | Qty: {o['amount']} | Price: {o.get('price', 'market')}")
        
    # Cancel them
    if orders:
        for o in orders:
            exchange.cancel_order(o['id'], 'DOGE/USDT:USDT')
            print(f"Cancelled order {o['id']}")
        print(f"\nTotal cancelled: {len(orders)}")
    else:
        print('No DOGE orders to cancel')
except Exception as e:
    print(f"Error: {e}")
