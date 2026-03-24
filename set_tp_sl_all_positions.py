import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

# CONFIG - AGGRESSIVE MODE
STOP_LOSS_PCT = 0.015   # 1.5% SL (tighter)
TAKE_PROFIT_PCT = 0.01  # 1% TP (faster profits)
MARGIN_MODE = 'ISOLATED'
LEVERAGE = 3

symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT',
           'DOGE/USDT:USDT', 'XRP/USDT:USDT', 'LINK/USDT:USDT', 'BCH/USDT:USDT']

print('=' * 60)
print('SETTING TP/SL FOR ALL OPEN POSITIONS')
print('=' * 60)

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
        side = pos['side'].upper()
        
        print(f"\n{symbol} {side}")
        print(f"  Size: {contracts}")
        print(f"  Entry: ${entry:.4f}")
        
        # Calculate TP/SL
        if side == 'SHORT':
            stop_loss = entry * (1 + STOP_LOSS_PCT)
            take_profit = entry * (1 - TAKE_PROFIT_PCT)
            close_side = 'buy'
        else:
            stop_loss = entry * (1 - STOP_LOSS_PCT)
            take_profit = entry * (1 + TAKE_PROFIT_PCT)
            close_side = 'sell'
        
        print(f"  SL: ${stop_loss:.4f} ({STOP_LOSS_PCT*100:.1f}%)")
        print(f"  TP: ${take_profit:.4f} ({TAKE_PROFIT_PCT*100:.1f}%)")
        
        # Cancel existing orders first
        try:
            exchange.cancel_all_orders(symbol)
            print("  Cancelled existing orders")
        except:
            pass
        
        # Set TP (limit order)
        try:
            exchange.create_order(
                symbol=symbol,
                type='limit',
                side=close_side,
                amount=contracts,
                price=round(take_profit, 4),
                params={'reduceOnly': True}
            )
            print(f"  [OK] TP set: ${take_profit:.4f}")
        except Exception as e:
            print(f"  [ERROR] TP: {e}")
        
        # Set SL (stop market)
        try:
            exchange.create_order(
                symbol=symbol,
                type='market',
                side=close_side,
                amount=contracts,
                params={
                    'triggerPrice': round(stop_loss, 4),
                    'triggerDirection': 'ascending' if side == 'SHORT' else 'descending',
                    'reduceOnly': True
                }
            )
            print(f"  [OK] SL set: ${stop_loss:.4f}")
        except Exception as e:
            print(f"  [ERROR] SL: {e}")
        
    except Exception as e:
        pass

print('\n' + '=' * 60)
print('TP/SL SETUP COMPLETE')
print('=' * 60)
