import ccxt
import os
from dotenv import load_dotenv
load_dotenv()

exchange = ccxt.bybit({
    'apiKey': os.getenv('BYBIT_API_KEY'),
    'secret': os.getenv('BYBIT_API_SECRET'),
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

symbols = ["NEAR/USDT:USDT", "DOGE/USDT:USDT", "ETH/USDT:USDT"]

for symbol in symbols:
    print(f"\n=== {symbol} ===")
    side = "short"
    
    # Get current price - convert NEAR/USDT:USDT to NEAR/USDT
    ticker = exchange.fetch_ticker(symbol.split(':')[0])
    current_price = ticker['last']
    print(f"Current price: {current_price}")
    
    # For short: TP below entry, SL above entry
    tp_price = round(current_price * 0.975, 4)
    sl_price = round(current_price * 1.025, 4)
    trailing = round(current_price * 0.01, 4)
    
    print(f"TP: {tp_price}, SL: {sl_price}, Trailing: {trailing}")
    
    # Get precision
    sym_for_prec = symbol.replace(':USDT', '')
    print(f"Symbol for prec: {sym_for_prec}")
    tp_str = str(exchange.price_to_precision(sym_for_prec, tp_price))
    sl_str = str(exchange.price_to_precision(sym_for_prec, sl_price))
    trail_str = str(exchange.price_to_precision(sym_for_prec, trailing))
    
    print(f"TP str: {tp_str}, SL str: {sl_str}, Trail str: {trail_str}")
    
    # Set TP/SL with trailing stop
    bybit_symbol = symbol.replace('/USDT:USDT', 'USDT')
    print(f"Bybit symbol: {bybit_symbol}")
    
    params = {
        'symbol': bybit_symbol,
        'category': 'linear',
        'takeProfit': tp_str,
        'stopLoss': sl_str,
        'trailingStop': trail_str,
        'tpTriggerBy': 'LastPrice',
        'slTriggerBy': 'LastPrice',
        'tpslMode': 'Full',
    }
    
    try:
        response = exchange.privatePostV5PositionTradingStop(params)
        print(f"Response: {response}")
    except Exception as e:
        print(f"Exception: {e}")
