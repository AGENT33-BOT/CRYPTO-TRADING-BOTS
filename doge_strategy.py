"""
DOGE Only Strategy - Based on Trade History
DOGE: 100% win rate, +$9.67 profit in 15 trades
"""
import ccxt
import time
import requests
from datetime import datetime

BYBIT_API_KEY = "KfmiIdWd16hG18v2O7"
BYBIT_SECRET = "VTVePZIz2GEqyy6AcvwPVcaRNBRolmXkuWlZ"
TELEGRAM_TOKEN = "8249656817:AAFAI3oulkDWJZHJ7STSYlDfK-_UJCPo-7U"
TELEGRAM_CHAT_ID = "5804173449"

# STRATEGY BASED ON HISTORY
SYMBOLS = ['DOGEUSDT']  # Only DOGE - 100% win rate!
MAX_POSITIONS = 1
POSITION_SIZE_PERCENT = 5  # Small position
TP_PERCENT = 1.5  # Small, consistent profits
SL_PERCENT = 1.0  # Tight stop loss
TRAIL_PERCENT = 0.5

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

def set_tpsl(symbol, side, entry_price):
    try:
        clean_sym = symbol.replace('/USDT', '')
        
        if side in ['buy', 'long']:
            tp = round(entry_price * (1 + TP_PERCENT/100), 6)
            sl = round(entry_price * (1 - SL_PERCENT/100), 6)
            trail = round(entry_price * (TRAIL_PERCENT/100), 6)
            active = round(entry_price * (1 + TRAIL_PERCENT/100), 6)
        else:
            tp = round(entry_price * (1 - TP_PERCENT/100), 6)
            sl = round(entry_price * (1 + SL_PERCENT/100), 6)
            trail = round(entry_price * (TRAIL_PERCENT/100), 6)
            active = round(entry_price * (1 - TRAIL_PERCENT/100), 6)
        
        result = bybit.privatePostV5PositionTradingStop({
            'category': 'linear',
            'symbol': clean_sym,
            'takeProfit': str(tp),
            'stopLoss': str(sl),
            'trailingStop': str(trail),
            'activePrice': str(active),
            'tpslMode': 'Full'
        })
        return result.get('retCode') == 0
    except:
        return False

def get_indicators(symbol):
    try:
        # Use 1h for more reliable signals
        ohlcv = bybit.fetch_ohlcv(symbol, '1h', limit=50)
        closes = [c[4] for c in ohlcv]
        
        if len(closes) < 20:
            return None
        
        price = closes[-1]
        
        # RSI
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        avg_gain = sum(gains[-14:]) / 14
        avg_loss = sum(losses[-14:]) / 14
        rsi = 100 - (100 / (1 + avg_gain/(avg_loss+0.0001)))
        
        # MA
        ma20 = sum(closes[-20:]) / 20
        
        signals = []
        if rsi < 25:
            signals.append('DEEP_OVERSOLD')
        elif rsi < 35:
            signals.append('OVERSOLD')
        if price < ma20:
            signals.append('BELOW_MA')
        
        return {'rsi': rsi, 'price': price, 'ma20': ma20, 'signals': signals}
    except:
        return None

def analyze_and_trade():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] DOGE Strategy...")
    
    open_positions = get_open_positions()
    
    if len(open_positions) >= MAX_POSITIONS:
        print(f"Max positions: {len(open_positions)}")
        return
    
    balance = get_balance()
    
    for symbol in SYMBOLS:
        has_position = any(symbol in p['symbol'] for p in open_positions)
        if has_position:
            print(f"Already have {symbol}")
            continue
        
        indicators = get_indicators(symbol)
        if not indicators:
            continue
        
        rsi = indicators['rsi']
        print(f"DOGE: RSI={rsi:.1f} Price=${indicators['price']}")
        
        # Conservative: Wait for deep oversold
        should_buy = 'DEEP_OVERSOLD' in indicators['signals'] or ('OVERSOLD' in indicators['signals'] and 'BELOW_MA' in indicators['signals'])
        
        if should_buy:
            try:
                size = (balance * POSITION_SIZE_PERCENT / 100) / indicators['price']
                size = round(size, 0)  # Round for DOGE
                
                if size < 100:
                    print("Position too small")
                    continue
                
                print(f"Buying DOGE...")
                
                order = bybit.create_market_order(symbol=symbol, side='buy', amount=size)
                
                time.sleep(2)
                set_tpsl(symbol, 'long', indicators['price'])
                
                msg = f"DOGE Strategy BUY\nPrice: ${indicators['price']}\nSize: {size}\nTP: {TP_PERCENT}% | SL: {SL_PERCENT}%"
                print(msg)
                send_telegram(msg)
                
            except Exception as e:
                print(f"Error: {e}")

def run_bot():
    print("DOGE Strategy Bot Starting...")
    print("Based on history: DOGE 100% win rate!")
    send_telegram("DOGE Strategy Started!\nOnly DOGE\n100% win rate in history\nTP 1.5% | SL 1%")
    
    while True:
        try:
            # Check positions
            open_positions = get_open_positions()
            for p in open_positions:
                info = p.get('info', {})
                if info.get('takeProfit', '0') == '0':
                    entry = float(p.get('entryPrice', 0))
                    if entry > 0:
                        set_tpsl(p['symbol'], p['side'], entry)
            
            # Trade
            analyze_and_trade()
            
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(600)  # Check every 10 minutes

if __name__ == "__main__":
    run_bot()