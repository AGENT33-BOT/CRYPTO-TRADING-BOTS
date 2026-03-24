import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

bybit = ccxt.bybit({
    'apiKey': os.getenv('BYBIT_API_KEY'),
    'secret': os.getenv('BYBIT_API_SECRET'),
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

positions = bybit.fetch_positions()

for p in positions:
    if float(p.get('contracts', 0)) > 0:
        symbol = p['symbol']
        side = p['side']
        entry = p['entryPrice']
        
        # Get current price
        ticker = bybit.fetch_ticker(symbol.split(':')[0])
        current = ticker['last']
        
        if side == 'long':
            tp = round(current * 1.025, 4)
            sl = round(current * 0.975, 4)
            trailing = round(current * 0.01, 4)
            active = round(current * 1.01, 4)
        else:
            tp = round(current * 0.975, 4)
            sl = round(current * 1.025, 4)
            trailing = round(current * 0.01, 4)
            active = round(current * 0.99, 4)
        
        bybit_sym = symbol.replace('/USDT:USDT', 'USDT')
        
        params = {
            'symbol': bybit_sym,
            'category': 'linear',
            'takeProfit': str(tp),
            'stopLoss': str(sl),
            'trailingStop': str(trailing),
            'activePrice': str(active),
            'tpTriggerBy': 'LastPrice',
            'slTriggerBy': 'LastPrice',
            'tpslMode': 'Full',
        }
        
        print(f'Setting {symbol}: TP={tp} SL={sl} Trail={trailing}')
        
        r = bybit.privatePostV5PositionTradingStop(params)
        print(f'RetCode: {r.get("retCode")} - {r.get("retMsg")}')
        print()
