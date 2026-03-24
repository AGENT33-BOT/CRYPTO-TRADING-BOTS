"""
AI Trading Bot - Fixed with proper TP/SL
"""
import ccxt
import time
import requests
from datetime import datetime

BYBIT_API_KEY = "KfmiIdWd16hG18v2O7"
BYBIT_SECRET = "VTVePZIz2GEqyy6AcvwPVcaRNBRolmXkuWlZ"
TELEGRAM_TOKEN = "8249656817:AAFAI3oulkDWJZHJ7STSYlDfK-_UJCPo-7U"
TELEGRAM_CHAT_ID = "5804173449"

SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'NEARUSDT', 'LINKUSDT', 'DOGEUSDT']
MAX_POSITIONS = 3
POSITION_SIZE_PERCENT = 10
TP_PERCENT = 2.5
SL_PERCENT = 2.5
TRAIL_PERCENT = 1.0

bybit = ccxt.bybit({
    'apiKey': BYBIT_API_KEY,
    'secret': BYBIT_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

def send_telegram(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                     json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=10)
    except:
        pass

def get_balance():
    try:
        return bybit.fetch_balance()['USDT']['total']
    except:
        return 0

def get_open_positions():
    try:
        return [p for p in bybit.fetch_positions() if float(p.get('contracts', 0)) > 0]
    except:
        return []

def set_tpsl_after_trade(symbol, side, entry_price):
    """Set TP/SL immediately after trade using v5 API"""
    try:
        clean_sym = symbol.replace('/USDT', '')
        
        if side == 'buy' or side == 'long':
            tp = round(entry_price * (1 + TP_PERCENT/100), 4)
            sl = round(entry_price * (1 - SL_PERCENT/100), 4)
            trail = round(entry_price * (TRAIL_PERCENT/100), 4)
            active = round(entry_price * (1 + TRAIL_PERCENT/100), 4)
        else:
            tp = round(entry_price * (1 - TP_PERCENT/100), 4)
            sl = round(entry_price * (1 + SL_PERCENT/100), 4)
            trail = round(entry_price * (TRAIL_PERCENT/100), 4)
            active = round(entry_price * (1 - TRAIL_PERCENT/100), 4)
        
        result = bybit.privatePostV5PositionTradingStop({
            'category': 'linear',
            'symbol': clean_sym,
            'takeProfit': str(tp),
            'stopLoss': str(sl),
            'trailingStop': str(trail),
            'activePrice': str(active),
            'tpslMode': 'Full'
        })
        
        if result.get('retCode') == 0:
            return True, tp, sl
        else:
            print(f"TP/SL Error: {result.get('retMsg')}")
            return False, tp, sl
    except Exception as e:
        print(f"TP/SL Exception: {e}")
        return False, 0, 0

def analyze_and_trade():
    print("Analyzing market...")
    
    open_positions = get_open_positions()
    
    if len(open_positions) >= MAX_POSITIONS:
        print(f"Max positions: {len(open_positions)}")
        return
    
    balance = get_balance()
    print(f"Balance: ${balance:.2f}")
    
    for symbol in SYMBOLS:
        has_position = any(symbol in p['symbol'] for p in open_positions)
        if has_position:
            continue
        
        try:
            ohlcv = bybit.fetch_ohlcv(symbol, '15m', limit=50)
            closes = [c[4] for c in ohlcv]
            
            if len(closes) < 20:
                continue
            
            price = closes[-1]
            
            # RSI
            deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
            gains = [d if d > 0 else 0 for d in deltas]
            losses = [-d if d < 0 else 0 for d in deltas]
            avg_gain = sum(gains[-14:]) / 14
            avg_loss = sum(losses[-14:]) / 14
            rsi = 100 - (100 / (1 + avg_gain/(avg_loss+0.0001)))
            
            ma20 = sum(closes[-20:]) / 20
            ma50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else ma20
            
            signals = []
            if rsi < 30:
                signals.append('RSI_OVERSOLD')
            elif rsi > 70:
                signals.append('RSI_OVERBOUGHT')
            if price > ma20:
                signals.append('ABOVE_MA20')
            if ma20 > ma50:
                signals.append('TREND_UP')
            
            print(f"{symbol}: RSI={rsi:.1f} Signals={signals}")
            
            should_buy = ('RSI_OVERSOLD' in signals or ('ABOVE_MA20' in signals and 'TREND_UP' in signals))
            
            if should_buy:
                size = (balance * POSITION_SIZE_PERCENT / 100) / price
                size = round(size, 3)
                
                if size < 0.001:
                    continue
                
                print(f"Buying {symbol}...")
                
                # Place order
                order = bybit.create_market_order(symbol=symbol, side='buy', amount=size)
                
                # Set TP/SL IMMEDIATELY
                time.sleep(1)  # Wait for order to settle
                success, tp, sl = set_tpsl_after_trade(symbol, 'long', price)
                
                msg = f" BUY {symbol}\nPrice: ${price:.4f}\nSize: {size}\nTP: {tp} | SL: {sl}"
                print(msg)
                send_telegram(msg)
                
        except Exception as e:
            print(f"Error {symbol}: {e}")
        
        time.sleep(1)

def run_bot():
    print("AI Trading Bot starting...")
    send_telegram("AI Trading Bot started with TP/SL protection!")
    
    while True:
        try:
            analyze_and_trade()
            time.sleep(300)  # 5 min
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_bot()