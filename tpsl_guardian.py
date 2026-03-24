"""
TP/SL Guardian - Fixed symbol format
"""
import ccxt
import os
import requests

BYBIT_API_KEY = os.getenv('BYBIT_API_KEY', 'KfmiIdWd16hG18v2O7')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET', 'VTVePZIz2GEqyy6AcvwPVcaRNBRolmXkuWlZ')
TELEGRAM_TOKEN = '8249656817:AAFAI3oulkDWJZHJ7STSYlDfK-_UJCPo-7U'
TELEGRAM_CHAT_ID = '5804173449'

def send_telegram(msg):
    try:
        requests.post(f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage',
                     json={'chat_id': TELEGRAM_CHAT_ID, 'text': msg}, timeout=10)
    except:
        pass

def set_tpsl(bybit, symbol_raw, side, entry):
    """Set TP/SL - FIXED symbol format"""
    # DOGE/USDT:USDT -> DOGEUSDT
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
    alerts = []
    
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
                    sym_name = symbol.replace('/USDT:USDT', '')
                    msg = f"PROTECTED: {sym_name} TP:{tp_price} SL:{sl_price}"
                    print(msg)
                    alerts.append(msg)
                    fixed += 1
    
    if fixed > 0:
        send_telegram("TP/SL GUARDIAN:\n" + "\n".join(alerts))
    else:
        print("All protected")

if __name__ == "__main__":
    check_and_fix()