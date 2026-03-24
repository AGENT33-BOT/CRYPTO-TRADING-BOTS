import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

exchange = ccxt.bybit({
    'apiKey': os.getenv('BYBIT_API_KEY', 'KcyG0x0rDBLCXGsvHe'),
    'secret': os.getenv('BYBIT_API_SECRET', 'VCIzvKYTZJGqiVM0He2VFGqqqqq'),
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

symbols = ['NEAR/USDT:USDT', 'ETH/USDT:USDT', 'XRP/USDT:USDT']

for sym in symbols:
    try:
        positions = exchange.fetch_positions([sym])
        for pos in positions:
            size = float(pos.get('contracts', 0))
            side = pos.get('side', '')
            if size > 0 and side == 'short':
                print(f'Closing {sym} SHORT (size: {size})')
                order = exchange.create_market_buy_order(sym, size)
                print(f'✅ {sym} SHORT closed')
            elif size > 0:
                print(f'ℹ️ {sym} is {side}, size: {size} (keeping)')
            else:
                print(f'ℹ️ {sym} no position')
    except Exception as e:
        print(f'❌ {sym} error: {str(e)[:80]}')

print('Done')
