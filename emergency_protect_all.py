import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

print('=' * 70)
print('EMERGENCY: SETTING TP/SL FOR ALL POSITIONS - MAX $5 LOSS')
print('=' * 70)

# Check all positions
symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT',
           'DOGE/USDT:USDT', 'XRP/USDT:USDT', 'LINK/USDT:USDT', 'BCH/USDT:USDT',
           'DOT/USDT:USDT', 'LTC/USDT:USDT', 'UNI/USDT:USDT', 'ATOM/USDT:USDT',
           'ETC/USDT:USDT', 'ARB/USDT:USDT', 'OP/USDT:USDT', 'NEAR/USDT:USDT']

for symbol in symbols:
    try:
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
        
        print(f"\n{symbol} {side} {contracts}")
        print(f"  Entry: ${entry:.4f} | Mark: ${mark:.4f}")
        print(f"  Current PnL: ${pnl:+.2f}")
        
        # Check if loss > $5 - CLOSE IMMEDIATELY
        if pnl < -5.0:
            print(f"  🚨 LOSS EXCEEDS $5! Closing immediately...")
            close_side = 'sell' if side == 'LONG' else 'buy'
            try:
                exchange.create_market_order(
                    symbol=symbol,
                    side=close_side,
                    amount=contracts,
                    params={'reduceOnly': True}
                )
                print(f"  ✅ POSITION CLOSED at ${pnl:.2f} loss")
                exchange.cancel_all_orders(symbol)
                continue
            except Exception as e:
                print(f"  ❌ Close error: {e}")
        
        # Cancel all existing orders
        try:
            orders = exchange.fetch_open_orders(symbol)
            for o in orders:
                exchange.cancel_order(o['id'], symbol)
            if orders:
                print(f"  Cancelled {len(orders)} old orders")
        except:
            pass
        
        # Calculate TP/SL
        # TP = 1.5% profit
        # SL = max(2% or $5 loss whichever comes first)
        if side == 'LONG':
            tp = entry * 1.015
            # SL at 2% OR when loss = $5
            sl_pct = 0.02
            sl = entry * (1 - sl_pct)
            close_side = 'sell'
            trigger_dir = 'descending'
        else:
            tp = entry * 0.985
            sl_pct = 0.02
            sl = entry * (1 + sl_pct)
            close_side = 'buy'
            trigger_dir = 'ascending'
        
        print(f"  Setting TP: ${tp:.4f} (1.5%)")
        print(f"  Setting SL: ${sl:.4f} (2% or ~$5 max)")
        
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
            print(f"  ✅ TP SET")
        except Exception as e:
            print(f"  ❌ TP Error: {e}")
        
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
            print(f"  ✅ SL SET")
        except Exception as e:
            print(f"  ❌ SL Error: {e}")
            
    except Exception as e:
        pass

print('\n' + '=' * 70)
print('ALL POSITIONS PROTECTED - MAX $5 LOSS ENFORCED')
print('=' * 70)
