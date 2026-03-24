import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

symbol = 'DOT/USDT:USDT'

print('=' * 60)
print(f'CLEANING UP {symbol} ORDERS')
print('=' * 60)

try:
    # Get position
    positions = exchange.fetch_positions([symbol])
    if positions and len(positions) > 0:
        pos = positions[0]
        contracts = float(pos.get('contracts', 0))
        entry = float(pos.get('entryPrice', 0))
        side = pos['side'].upper()
        
        print(f"Position: {side} {contracts}")
        print(f"Entry: ${entry:.4f}")
        
        # Calculate new TP/SL at 1.5% / 2%
        if side == 'LONG':
            tp = entry * 1.015
            sl = entry * 0.98
            close_side = 'sell'
        else:
            tp = entry * 0.985
            sl = entry * 1.02
            close_side = 'buy'
        
        print(f"New TP (1.5%): ${tp:.4f}")
        print(f"New SL (2%): ${sl:.4f}")
        
        # Cancel ALL existing orders
        orders = exchange.fetch_open_orders(symbol)
        print(f"\nCancelling {len(orders)} existing orders...")
        
        for order in orders:
            try:
                exchange.cancel_order(order['id'], symbol)
                print(f"  ❌ Cancelled {order['type']} order")
            except:
                pass
        
        # Set fresh TP (limit order)
        print(f"\nSetting fresh orders...")
        exchange.create_order(
            symbol=symbol,
            type='limit',
            side=close_side,
            amount=contracts,
            price=round(tp, 4),
            params={'reduceOnly': True}
        )
        print(f"  ✅ TP set: ${tp:.4f}")
        
        # Set fresh SL (stop market)
        exchange.create_order(
            symbol=symbol,
            type='market',
            side=close_side,
            amount=contracts,
            params={
                'triggerPrice': round(sl, 4),
                'triggerDirection': 'descending' if side == 'LONG' else 'ascending',
                'reduceOnly': True
            }
        )
        print(f"  ✅ SL set: ${sl:.4f}")
        
        print("\n" + "=" * 60)
        print("CLEANUP COMPLETE")
        print("=" * 60)
        
    else:
        print("No position found - cancelling all orders...")
        orders = exchange.fetch_open_orders(symbol)
        for order in orders:
            try:
                exchange.cancel_order(order['id'], symbol)
                print(f"  ❌ Cancelled {order['type']} order")
            except:
                pass
        
except Exception as e:
    print(f"Error: {e}")
