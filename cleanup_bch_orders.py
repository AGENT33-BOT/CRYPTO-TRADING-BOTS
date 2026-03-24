import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

symbol = 'BCH/USDT:USDT'

print('=' * 60)
print(f'CLEANING UP EXCESS ORDERS FOR {symbol}')
print('=' * 60)

try:
    # Get open orders
    orders = exchange.fetch_open_orders(symbol)
    print(f"\nFound {len(orders)} open orders:")
    
    # Separate TP (limit) and SL (market/stop) orders
    limit_orders = []
    market_orders = []
    
    for order in orders:
        order_type = order['type']
        order_id = order['id']
        price = order.get('price', 'N/A')
        
        print(f"  {order_type.upper()} | ID: {order_id[:20]}... | Price: {price}")
        
        if order_type == 'limit':
            limit_orders.append(order)
        else:
            market_orders.append(order)
    
    print(f"\n  Limit orders (TP): {len(limit_orders)}")
    print(f"  Market orders (SL): {len(market_orders)}")
    
    # Keep only 1 TP (limit) and 1 SL (market), cancel the rest
    # Sort by price to identify best TP (lowest for SHORT)
    if len(limit_orders) > 1:
        # Sort by price - keep the best TP
        limit_orders.sort(key=lambda x: float(x.get('price') or 0))
        to_cancel = limit_orders[1:]  # Keep first, cancel rest
        
        print(f"\n  Cancelling {len(to_cancel)} excess limit orders...")
        for order in to_cancel:
            try:
                exchange.cancel_order(order['id'], symbol)
                print(f"    [CANCELLED] Limit order {order['id'][:15]}...")
            except Exception as e:
                print(f"    [ERROR] {e}")
    
    # For market orders (SL), keep only the most recent one
    if len(market_orders) > 1:
        # Sort by timestamp - keep most recent
        market_orders.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        to_cancel = market_orders[1:]  # Keep first (most recent)
        
        print(f"\n  Cancelling {len(to_cancel)} excess market orders...")
        for order in to_cancel:
            try:
                exchange.cancel_order(order['id'], symbol)
                print(f"    [CANCELLED] Market order {order['id'][:15]}...")
            except Exception as e:
                print(f"    [ERROR] {e}")
    
    print('\n' + '=' * 60)
    print('BCH ORDER CLEANUP COMPLETE')
    print('=' * 60)
    
    # Verify
    remaining = exchange.fetch_open_orders(symbol)
    print(f"\nRemaining orders: {len(remaining)}")
    for order in remaining:
        print(f"  {order['type'].upper()} @ {order.get('price', 'MARKET')}")
    
except Exception as e:
    print(f"[ERROR] {e}")
