import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

# All trading pairs
symbols = [
    'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT',
    'DOGE/USDT:USDT', 'XRP/USDT:USDT', 'LINK/USDT:USDT', 'BCH/USDT:USDT',
    'DOT/USDT:USDT', 'LTC/USDT:USDT', 'UNI/USDT:USDT', 'ATOM/USDT:USDT',
    'ETC/USDT:USDT', 'ARB/USDT:USDT', 'OP/USDT:USDT', 'NEAR/USDT:USDT',
    'APT/USDT:USDT', 'SUI/USDT:USDT', 'AVAX/USDT:USDT'
]

print('=' * 70)
print('COMPLETE POSITION & TP/SL AUDIT')
print('=' * 70)

protected_count = 0
unprotected_count = 0

for symbol in symbols:
    try:
        # Check position
        positions = exchange.fetch_positions([symbol])
        if not positions or len(positions) == 0:
            continue
        
        pos = positions[0]
        contracts = float(pos.get('contracts', 0))
        
        if contracts <= 0:
            continue
        
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
        
        # Separate TP (limit) and SL (market/stop)
        limit_orders = [o for o in orders if o['type'] == 'limit']
        market_orders = [o for o in orders if o['type'] != 'limit']
        
        if len(limit_orders) >= 1 and len(market_orders) >= 1:
            print(f"  ✅ PROTECTED: {len(limit_orders)} TP + {len(market_orders)} SL")
            if limit_orders:
                print(f"     TP: ${limit_orders[0].get('price', 'N/A')}")
            protected_count += 1
        elif len(limit_orders) >= 1:
            print(f"  ⚠️  PARTIAL: Has TP ({len(limit_orders)}) but NO SL!")
            unprotected_count += 1
            # Set SL
            if side == 'LONG':
                sl = entry * 0.98
                close_side = 'sell'
                trigger_dir = 'descending'
            else:
                sl = entry * 1.02
                close_side = 'buy'
                trigger_dir = 'ascending'
            
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
                print(f"     ✅ SL SET: ${sl:.4f}")
            except Exception as e:
                print(f"     ❌ SL ERROR: {e}")
                
        elif len(market_orders) >= 1:
            print(f"  ⚠️  PARTIAL: Has SL ({len(market_orders)}) but NO TP!")
            unprotected_count += 1
            # Set TP
            if side == 'LONG':
                tp = entry * 1.015
                close_side = 'sell'
            else:
                tp = entry * 0.985
                close_side = 'buy'
            
            try:
                exchange.create_order(
                    symbol=symbol,
                    type='limit',
                    side=close_side,
                    amount=contracts,
                    price=round(tp, 4),
                    params={'reduceOnly': True}
                )
                print(f"     ✅ TP SET: ${tp:.4f}")
            except Exception as e:
                print(f"     ❌ TP ERROR: {e}")
        else:
            print(f"  ❌ UNPROTECTED: NO TP/SL!")
            unprotected_count += 1
            
            # Calculate and set both
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
            
            print(f"     Setting TP: ${tp:.4f} | SL: ${sl:.4f}")
            
            # Set TP
            try:
                exchange.create_order(
                    symbol=symbol,
                    type='limit',
                    side=close_side,
                    amount=contracts,
                    price=round(tp, 4),
                    params={'reduceOnly': True}
                )
                print(f"     ✅ TP SET")
            except Exception as e:
                print(f"     ❌ TP ERROR: {e}")
            
            # Set SL
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
                print(f"     ✅ SL SET")
            except Exception as e:
                print(f"     ❌ SL ERROR: {e}")
                
    except Exception as e:
        pass

print('\n' + '=' * 70)
print(f'PROTECTED: {protected_count} | UNPROTECTED/FIXED: {unprotected_count}')
print('=' * 70)
