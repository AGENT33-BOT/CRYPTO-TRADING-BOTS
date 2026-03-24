import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

symbols = ['ADA/USDT:USDT', 'SOL/USDT:USDT']

print('=' * 60)
print('SETTING TP/SL FOR ADA AND SOL')
print('=' * 60)

for symbol in symbols:
    try:
        positions = exchange.fetch_positions([symbol])
        if positions and len(positions) > 0:
            pos = positions[0]
            contracts = float(pos.get('contracts', 0))
            
            if contracts > 0:
                entry = float(pos.get('entryPrice', 0))
                side = pos['side'].upper()
                
                print(f"\n{symbol} {side} {contracts}")
                print(f"Entry: ${entry:.4f}")
                
                # Calculate TP/SL at 1.5% / 2%
                if side == 'LONG':
                    tp = entry * 1.015
                    sl = entry * 0.98
                    close_side = 'sell'
                    trigger_dir = 'descending'
                else:
                    tp = entry * 0.985
                    sl = entry * 1.02
                    close_side = 'buy'
                    trigger_dir = 'ascending'
                
                print(f"TP (1.5%): ${tp:.4f}")
                print(f"SL (2%): ${sl:.4f}")
                
                # Cancel existing orders
                try:
                    orders = exchange.fetch_open_orders(symbol)
                    for o in orders:
                        exchange.cancel_order(o['id'], symbol)
                    print(f"Cancelled {len(orders)} old orders")
                except:
                    pass
                
                # Set TP (limit)
                try:
                    exchange.create_order(
                        symbol=symbol,
                        type='limit',
                        side=close_side,
                        amount=contracts,
                        price=round(tp, 4),
                        params={'reduceOnly': True}
                    )
                    print(f"✓ TP set: ${tp:.4f}")
                except Exception as e:
                    print(f"✗ TP error: {e}")
                
                # Set SL (stop market with trigger direction)
                try:
                    exchange.create_order(
                        symbol=symbol,
                        type='market',
                        side=close_side,
                        amount=contracts,
                        params={
                            'triggerPrice': round(sl, 4),
                            'triggerDirection': trigger_dir,
                            'reduceOnly': True
                        }
                    )
                    print(f"✓ SL set: ${sl:.4f}")
                except Exception as e:
                    print(f"✗ SL error: {e}")
                    
    except Exception as e:
        print(f"Error: {e}")

print('\n' + '=' * 60)
print('TP/SL SETUP COMPLETE')
print('=' * 60)
