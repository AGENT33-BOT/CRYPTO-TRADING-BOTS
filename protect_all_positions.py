import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

# Current positions
positions = [
    {'symbol': 'SOL/USDT:USDT', 'side': 'SHORT', 'entry': 75.1435, 'size': 6.3},
    {'symbol': 'BTC/USDT:USDT', 'side': 'SHORT', 'entry': 62305.43, 'size': 0.002},
    {'symbol': 'ADA/USDT:USDT', 'side': 'LONG', 'entry': 0.2433, 'size': 136.0}
]

STOP_LOSS_PCT = 0.02
TAKE_PROFIT_PCT = 0.04

print('=' * 60)
print('SETTING TP/SL PROTECTION')
print('=' * 60)

for pos in positions:
    symbol = pos['symbol']
    side = pos['side']
    entry = pos['entry']
    size = pos['size']
    
    print(f"\n{symbol} {side}")
    
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
        exchange.cancel_all_orders(symbol)
        
        # TP
        exchange.create_order(
            symbol=symbol, type='limit', side=close_side, amount=size,
            price=round(take_profit, 4), params={'reduceOnly': True}
        )
        print(f"  [OK] TP set")
        
        # SL
        exchange.create_order(
            symbol=symbol, type='market', side=close_side, amount=size,
            price=None, params={
                'triggerPrice': round(stop_loss, 4),
                'triggerDirection': 'ascending' if side == 'SHORT' else 'descending',
                'reduceOnly': True
            }
        )
        print(f"  [OK] SL set")
    except Exception as e:
        print(f"  [ERROR] {e}")

print('\n' + '=' * 60)
print('ALL POSITIONS PROTECTED')
print('=' * 60)
