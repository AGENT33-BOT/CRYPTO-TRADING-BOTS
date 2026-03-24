import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

SYMBOLS = [
    'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT',
    'DOGE/USDT:USDT', 'XRP/USDT:USDT', 'LINK/USDT:USDT', 'AVAX/USDT:USDT',
    'DOT/USDT:USDT', 'LTC/USDT:USDT', 'BCH/USDT:USDT', 'UNI/USDT:USDT',
    'ATOM/USDT:USDT', 'ETC/USDT:USDT', 'ARB/USDT:USDT', 'OP/USDT:USDT',
    'NEAR/USDT:USDT', 'APT/USDT:USDT', 'SUI/USDT:USDT'
]

print('=' * 60)
print('CLEANING UP ORPHANED ORDERS')
print('=' * 60)

total_cancelled = 0

for symbol in SYMBOLS:
    try:
        # Check position
        positions = exchange.fetch_positions([symbol])
        has_position = False
        
        if positions and len(positions) > 0:
            contracts = float(positions[0].get('contracts', 0))
            if contracts > 0:
                has_position = True
        
        if has_position:
            continue  # Skip - position exists
        
        # No position - check for orders
        orders = exchange.fetch_open_orders(symbol)
        
        if orders:
            print(f"\n{symbol}: No position but {len(orders)} order(s) found")
            
            for order in orders:
                try:
                    exchange.cancel_order(order['id'], symbol)
                    print(f"  [CANCELLED] {order['type']} order")
                    total_cancelled += 1
                except Exception as e:
                    print(f"  [ERROR] Could not cancel: {e}")
                    
    except Exception as e:
        pass

print('\n' + '=' * 60)
print(f'TOTAL ORPHANED ORDERS CANCELLED: {total_cancelled}')
print('=' * 60)
print("\nOrphan order cleaner is now running continuously...")
print("(Checks every 30 seconds automatically)")
