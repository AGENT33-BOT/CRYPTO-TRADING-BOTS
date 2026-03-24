import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

symbol = 'NEAR/USDT:USDT'

print(f"Closing position for {symbol}...")

try:
    exchange = ccxt.bybit({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })
    
    exchange.load_markets()
    
    # Get all positions
    positions = exchange.fetch_positions()
    
    for pos in positions:
        pos_symbol = pos.get('symbol', '')
        size = float(pos.get('contracts', 0) or 0)
        side = pos.get('side', '')
        
        if 'NEAR' in pos_symbol and size > 0:
            print(f"Found NEAR position: {size} contracts ({side})")
            
            # Cancel open orders
            try:
                exchange.cancel_all_orders(pos_symbol)
                print(f"Cancelled orders for {pos_symbol}")
            except Exception as e:
                print(f"Note: {e}")
            
            # Close position
            close_side = 'sell' if side == 'long' else 'buy'
            
            order = exchange.create_order(
                symbol=pos_symbol,
                type='market',
                side=close_side,
                amount=size,
                params={'reduceOnly': True}
            )
            
            pnl = float(pos.get('unrealizedPnl', 0) or 0)
            print(f"✅ Position closed: {order['id']}")
            print(f"   Realized PnL: ${pnl:.2f}")
            break
    else:
        print("No NEAR position found")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    print(traceback.format_exc())
