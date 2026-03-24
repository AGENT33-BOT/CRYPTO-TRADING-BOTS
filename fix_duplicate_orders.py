import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

def cleanup_symbol(symbol, position_size, side):
    """Clean up duplicate orders for a symbol"""
    print(f"\n{symbol}:")
    print(f"  Position: {side} {position_size}")
    
    try:
        orders = exchange.fetch_open_orders(symbol)
        if not orders:
            print("  No orders to clean")
            return
        
        print(f"  Found {len(orders)} orders - cleaning up...")
        
        # Separate limit (TP) and market/stop (SL) orders
        limit_orders = []
        market_orders = []
        
        for order in orders:
            if order['type'] == 'limit':
                limit_orders.append(order)
            else:
                market_orders.append(order)
        
        # For SHORT positions, TP is limit buy at lower price
        # We want to keep the LOWEST price limit order (best TP)
        if side == 'SHORT' and limit_orders:
            limit_orders.sort(key=lambda x: float(x.get('price') or 999999))
            best_tp = limit_orders[0]  # Lowest price
            to_cancel = limit_orders[1:]
            
            print(f"  Keeping TP at ${best_tp.get('price')} (lowest)")
            for order in to_cancel:
                try:
                    exchange.cancel_order(order['id'], symbol)
                    print(f"    Cancelled duplicate TP at ${order.get('price')}")
                except:
                    pass
        
        # For SL (market orders), keep only the most recent one
        if market_orders:
            # Sort by timestamp (newest first)
            market_orders.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            best_sl = market_orders[0]
            to_cancel = market_orders[1:]
            
            print(f"  Keeping SL (most recent)")
            for order in to_cancel:
                try:
                    exchange.cancel_order(order['id'], symbol)
                    print(f"    Cancelled duplicate SL")
                except:
                    pass
        
        # Now verify we have 1 TP and 1 SL with correct sizes
        remaining = exchange.fetch_open_orders(symbol)
        
        # Cancel all and recreate with correct size if needed
        if len(remaining) > 2 or any(float(o.get('amount', 0)) != position_size for o in remaining):
            print(f"  Recreating orders with correct size...")
            
            # Cancel all
            for order in remaining:
                try:
                    exchange.cancel_order(order['id'], symbol)
                except:
                    pass
            
            # Get position details for calculating TP/SL
            positions = exchange.fetch_positions([symbol])
            if positions and len(positions) > 0:
                pos = positions[0]
                entry = float(pos.get('entryPrice', 0))
                
                if entry > 0:
                    # Calculate prices
                    if side == 'SHORT':
                        tp_price = entry * 0.96  # 4% below entry
                        sl_price = entry * 1.02  # 2% above entry
                    else:
                        tp_price = entry * 1.04  # 4% above entry
                        sl_price = entry * 0.98  # 2% below entry
                    
                    close_side = 'buy' if side == 'SHORT' else 'sell'
                    
                    # Set TP (limit order)
                    exchange.create_order(
                        symbol=symbol,
                        type='limit',
                        side=close_side,
                        amount=position_size,
                        price=round(tp_price, 4),
                        params={'reduceOnly': True}
                    )
                    print(f"  [OK] TP set: ${tp_price:.4f}")
                    
                    # Set SL (stop market)
                    exchange.create_order(
                        symbol=symbol,
                        type='market',
                        side=close_side,
                        amount=position_size,
                        params={
                            'triggerPrice': round(sl_price, 4),
                            'triggerDirection': 'ascending' if side == 'SHORT' else 'descending',
                            'reduceOnly': True
                        }
                    )
                    print(f"  [OK] SL set: ${sl_price:.4f}")
        
        print("  Cleanup complete!")
        
    except Exception as e:
        print(f"  Error: {e}")

print('=' * 60)
print('CLEANING UP ALL DUPLICATE ORDERS')
print('=' * 60)

# XRP
cleanup_symbol('XRP/USDT:USDT', 169.0, 'SHORT')

# BCH
cleanup_symbol('BCH/USDT:USDT', 2.39, 'SHORT')

print('\n' + '=' * 60)
print('ALL CLEANUP COMPLETE')
print('=' * 60)
