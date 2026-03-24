import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

symbols = ['ADA/USDT:USDT', 'SOL/USDT:USDT', 'BTC/USDT:USDT', 'ETH/USDT:USDT', 
           'DOGE/USDT:USDT', 'XRP/USDT:USDT', 'DOT/USDT:USDT', 'BCH/USDT:USDT']

print('=' * 60)
print('CHECKING ALL POSITIONS FOR TP/SL STATUS')
print('=' * 60)

for symbol in symbols:
    try:
        # Check position
        positions = exchange.fetch_positions([symbol])
        if positions and len(positions) > 0:
            pos = positions[0]
            contracts = float(pos.get('contracts', 0))
            
            if contracts > 0:
                entry = float(pos.get('entryPrice', 0))
                mark = float(pos.get('markPrice', 0))
                side = pos['side'].upper()
                pnl = float(pos.get('unrealizedPnl', 0))
                
                print(f"\n{symbol} {side}")
                print(f"  Size: {contracts}")
                print(f"  Entry: ${entry:.4f}")
                print(f"  Mark: ${mark:.4f}")
                print(f"  PnL: ${pnl:+.2f}")
                
                # Check orders
                orders = exchange.fetch_open_orders(symbol)
                tp_sl_count = len(orders)
                
                if tp_sl_count >= 2:
                    print(f"  TP/SL: {tp_sl_count} orders (PROTECTED)")
                elif tp_sl_count == 1:
                    print(f"  TP/SL: 1 order (INCOMPLETE - needs SL)")
                else:
                    print(f"  TP/SL: NONE - SETTING NOW...")
                    
                    # Calculate TP/SL at 1.5% / 2%
                    if side == 'LONG':
                        tp = entry * 1.015
                        sl = entry * 0.98
                        close_side = 'sell'
                    else:
                        tp = entry * 0.985
                        sl = entry * 1.02
                        close_side = 'buy'
                    
                    # Set TP
                    try:
                        exchange.create_order(symbol, 'limit', close_side, contracts, round(tp, 4), {'reduceOnly': True})
                        print(f"    -> TP set: ${tp:.4f}")
                    except Exception as e:
                        print(f"    -> TP error: {e}")
                    
                    # Set SL
                    try:
                        exchange.create_order(symbol, 'market', close_side, contracts, params={'triggerPrice': round(sl, 4), 'reduceOnly': True})
                        print(f"    -> SL set: ${sl:.4f}")
                    except Exception as e:
                        print(f"    -> SL error: {e}")
                    
    except Exception as e:
        pass

print('\n' + '=' * 60)
