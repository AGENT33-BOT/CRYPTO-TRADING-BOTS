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
print(f'CLOSING BCH POSITION - TOO MUCH LOSS')
print('=' * 60)

try:
    positions = exchange.fetch_positions([symbol])
    if positions and len(positions) > 0:
        pos = positions[0]
        contracts = float(pos.get('contracts', 0))
        side = pos['side']
        pnl = float(pos.get('unrealizedPnl', 0))
        
        if contracts > 0:
            print(f"Position: {side.upper()} {contracts} BCH")
            print(f"Current Loss: ${pnl:.2f}")
            
            # Close immediately
            close_side = 'buy' if side == 'short' else 'sell'
            order = exchange.create_market_order(
                symbol=symbol,
                side=close_side,
                amount=contracts,
                params={'reduceOnly': True}
            )
            
            print(f"\n[OK] Position CLOSED: {order['id']}")
            print(f"Loss Stopped: ${pnl:.2f}")
            
            # Cancel all orders
            try:
                exchange.cancel_all_orders(symbol)
                print("[OK] All orders cancelled")
            except:
                pass
        else:
            print("No position found")
    else:
        print("No position found")
        
except Exception as e:
    print(f"[ERROR] {e}")

print('\n' + '=' * 60)
print('BCH POSITION CLOSED')
print('=' * 60)
