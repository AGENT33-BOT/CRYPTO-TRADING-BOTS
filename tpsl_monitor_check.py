"""
TP/SL Monitor - Fixed version
"""
import ccxt
import os

BYBIT_API_KEY = os.getenv('BYBIT_API_KEY', 'KfmiIdWd16hG18v2O7')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET', 'VTVePZIz2GEqyy6AcvwPVcaRNBRolmXkuWlZ')

def set_tpsl(bybit, symbol_raw, side, entry):
    """Set TP/SL - FIXED symbol format"""
    sym = symbol_raw.replace('/USDT:USDT', '') + 'USDT'
    
    if side in ['buy', 'long']:
        tp = round(entry * 1.025, 4)
        sl = round(entry * 0.975, 4)
        trail = round(entry * 0.01, 4)
        active = round(entry * 1.01, 4)
    else:
        tp = round(entry * 0.975, 4)
        sl = round(entry * 1.025, 4)
        trail = round(entry * 0.01, 4)
        active = round(entry * 0.99, 4)
    
    r = bybit.privatePostV5PositionTradingStop({
        'category': 'linear',
        'symbol': sym,
        'takeProfit': str(tp),
        'stopLoss': str(sl),
        'trailingStop': str(trail),
        'activePrice': str(active),
        'tpslMode': 'Full'
    })
    return r.get('retCode') == 0, tp, sl

def check_and_fix():
    bybit = ccxt.bybit({
        'apiKey': BYBIT_API_KEY,
        'secret': BYBIT_API_SECRET,
        'options': {'defaultType': 'swap'}
    })
    
    positions = bybit.fetch_positions()
    fixed = 0
    
    for p in positions:
        size = float(p.get('contracts', 0))
        if size > 0:
            info = p.get('info', {})
            tp = info.get('takeProfit', '')
            
            if not tp or tp == '0':
                symbol = p['symbol']
                side = p['side']
                entry = float(p['entryPrice'])
                
                success, tp_price, sl_price = set_tpsl(bybit, symbol, side, entry)
                
                if success:
                    name = symbol.replace('/USDT:USDT', '')
                    print(f'FIXED: {name} TP:{tp_price} SL:{sl_price}')
                    fixed += 1
                else:
                    print(f'ERROR: {symbol}')
    
    if fixed > 0:
        print(f'Total fixed: {fixed}')
    else:
        print('All protected')

if __name__ == "__main__":
    check_and_fix()