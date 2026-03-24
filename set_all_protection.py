import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

# Positions to protect
positions = [
    {'symbol': 'SOL/USDT:USDT', 'side': 'SHORT', 'entry': 69.89, 'size': 1.0},
    {'symbol': 'ADA/USDT:USDT', 'side': 'SHORT', 'entry': 0.2307, 'size': 135.0},
    {'symbol': 'XRP/USDT:USDT', 'side': 'SHORT', 'entry': 1.1448, 'size': 452.8}
]

STOP_LOSS_PCT = 0.02  # 2%
TAKE_PROFIT_PCT = 0.04  # 4%

print('=' * 60)
print('SETTING TP/SL PROTECTION')
print('=' * 60)

for pos in positions:
    symbol = pos['symbol']
    side = pos['side']
    entry = pos['entry']
    size = pos['size']
    
    print(f"\n{symbol} {side}")
    print(f"  Entry: ${entry}")
    print(f"  Size: {size}")
    
    # Calculate TP/SL
    if side == 'SHORT':
        stop_loss = entry * (1 + STOP_LOSS_PCT)
        take_profit = entry * (1 - TAKE_PROFIT_PCT)
        close_side = 'buy'
    else:
        stop_loss = entry * (1 - STOP_LOSS_PCT)
        take_profit = entry * (1 + TAKE_PROFIT_PCT)
        close_side = 'sell'
    
    print(f"  SL: ${stop_loss:.4f}")
    print(f"  TP: ${take_profit:.4f}")
    
    try:
        # Cancel any existing orders first
        try:
            exchange.cancel_all_orders(symbol)
            print("  Cancelled existing orders")
        except:
            pass
        
        # Set Take Profit (limit order)
        try:
            tp_order = exchange.create_order(
                symbol=symbol,
                type='limit',
                side=close_side,
                amount=size,
                price=round(take_profit, 4),
                params={'reduceOnly': True}
            )
            print(f"  [OK] TP set: ${take_profit:.4f}")
        except Exception as e:
            print(f"  [ERROR] TP: {e}")
        
        # Set Stop Loss (trigger order)
        try:
            sl_order = exchange.create_order(
                symbol=symbol,
                type='market',
                side=close_side,
                amount=size,
                price=None,
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
        print(f"  [ERROR] {e}")

print('\n' + '=' * 60)
print('PROTECTION COMPLETE')
print('=' * 60)
