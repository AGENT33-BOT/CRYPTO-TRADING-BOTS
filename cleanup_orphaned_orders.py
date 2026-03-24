import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

symbols = [
    'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT', 
    'DOGE/USDT:USDT', 'XRP/USDT:USDT', 'LINK/USDT:USDT', 'AVAX/USDT:USDT',
    'DOT/USDT:USDT', 'LTC/USDT:USDT', 'BCH/USDT:USDT', 'UNI/USDT:USDT',
    'ATOM/USDT:USDT', 'ETC/USDT:USDT', 'ARB/USDT:USDT', 'OP/USDT:USDT',
    'NEAR/USDT:USDT', 'APT/USDT:USDT', 'SUI/USDT:USDT'
]

print('=' * 60)
print('CLEANING UP ORPHANED CONDITIONAL ORDERS')
print('=' * 60)

# Get current positions
positions = {}
for symbol in symbols:
    try:
        pos_list = exchange.fetch_positions([symbol])
        if pos_list and len(pos_list) > 0:
            pos = pos_list[0]
            contracts = float(pos.get('contracts', 0))
            if contracts > 0:
                positions[symbol] = contracts
    except:
        pass

print(f"\nActive positions: {len(positions)}")
for sym, size in positions.items():
    print(f"  {sym}: {size}")

# Check for orphaned orders
print('\n' + '-' * 60)
print('Checking for orphaned orders...')
print('-' * 60)

total_cancelled = 0

for symbol in symbols:
    try:
        # Get open orders
        orders = exchange.fetch_open_orders(symbol)
        
        # Check if position exists
        has_position = symbol in positions
        
        if orders:
            print(f"\n{symbol}:")
            print(f"  Position: {'YES' if has_position else 'NO'}")
            
            for order in orders:
                order_type = order['type']
                order_id = order['id']
                
                # If no position but has conditional orders, cancel them
                if not has_position:
                    try:
                        exchange.cancel_order(order_id, symbol)
                        print(f"  [CANCELLED] {order_type} order (orphaned)")
                        total_cancelled += 1
                    except Exception as e:
                        print(f"  [ERROR] Could not cancel: {e}")
                else:
                    print(f"  [ACTIVE] {order_type} order (has position)")
    except Exception as e:
        pass

print('\n' + '=' * 60)
print(f'TOTAL ORPHANED ORDERS CANCELLED: {total_cancelled}')
print('=' * 60)
