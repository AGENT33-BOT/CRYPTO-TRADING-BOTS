import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

print('=' * 60)
print('CHECKING ALL ORDERS AND POSITIONS')
print('=' * 60)

symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT',
           'DOGE/USDT:USDT', 'XRP/USDT:USDT', 'LINK/USDT:USDT', 'BCH/USDT:USDT',
           'DOT/USDT:USDT', 'LTC/USDT:USDT', 'ATOM/USDT:USDT', 'ARB/USDT:USDT']

total_orders = 0

for symbol in symbols:
    try:
        # Check position
        positions = exchange.fetch_positions([symbol])
        position_size = 0
        
        if positions and len(positions) > 0:
            position_size = float(positions[0].get('contracts', 0))
        
        # Check orders
        orders = exchange.fetch_open_orders(symbol)
        
        if position_size > 0:
            print(f"\n{symbol}: Position {position_size}")
            if orders:
                print(f"  Orders: {len(orders)}")
                for o in orders:
                    print(f"    - {o['type']} {o['side']} @ {o.get('price', 'MARKET')}")
            else:
                print("  ⚠️  NO ORDERS - Setting TP/SL now...")
                # Set TP/SL
                entry = float(positions[0].get('entryPrice', 0))
                side = positions[0]['side'].upper()
                
                if side == 'LONG':
                    tp = entry * 1.015  # 1.5% TP
                    sl = entry * 0.98   # 2% SL
                    close_side = 'sell'
                else:
                    tp = entry * 0.985  # 1.5% TP
                    sl = entry * 1.02   # 2% SL
                    close_side = 'buy'
                
                # Set TP
                exchange.create_order(symbol, 'limit', close_side, position_size, round(tp, 4), {'reduceOnly': True})
                print(f"    ✅ TP set: ${tp:.4f}")
                
                # Set SL
                exchange.create_order(symbol, 'market', close_side, position_size, params={'triggerPrice': round(sl, 4), 'reduceOnly': True})
                print(f"    ✅ SL set: ${sl:.4f}")
        
        elif orders:
            # No position but has orders - cancel them
            print(f"\n{symbol}: No position but {len(orders)} order(s)")
            for o in orders:
                try:
                    exchange.cancel_order(o['id'], symbol)
                    print(f"    ❌ Cancelled {o['type']} order")
                    total_orders += 1
                except Exception as e:
                    print(f"    ⚠️  Error: {e}")
                    
    except Exception as e:
        pass

print('\n' + '=' * 60)
print(f'TOTAL ORDERS CANCELLED: {total_orders}')
print('=' * 60)
