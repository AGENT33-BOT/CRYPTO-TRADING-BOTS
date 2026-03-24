import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

symbol = 'XRP/USDT:USDT'

print(f"Closing {symbol} position...")

try:
    # Get position info
    positions = exchange.fetch_positions([symbol])
    if positions and len(positions) > 0:
        pos = positions[0]
        contracts = float(pos.get('contracts', 0))
        side = pos['side']
        
        if contracts > 0:
            print(f"  Position: {side.upper()} {contracts} XRP")
            
            # Close position (opposite side)
            close_side = 'buy' if side == 'short' else 'sell'
            
            order = exchange.create_market_order(
                symbol=symbol,
                side=close_side,
                amount=contracts,
                params={'reduceOnly': True}
            )
            
            print(f"  [OK] Position closed: {order['id']}")
            
            # Cancel any remaining orders
            try:
                exchange.cancel_all_orders(symbol)
                print("  [OK] All orders cancelled")
            except:
                pass
        else:
            print("  No position found")
    else:
        print("  No position found")
        
except Exception as e:
    print(f"  [ERROR] {e}")

print("\nDone!")
