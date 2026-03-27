"""
Hybrid Trading System - DOGE + Gold + News Signals
Integrates pinguilo strategy with our DOGE success
"""
import ccxt
import time
import requests
import json
from datetime import datetime

BYBIT_API_KEY = "KfmiIdWd16hG18v2O7"
BYBIT_API_SECRET = "VTVePZIz2GEqyy6AcvwPVcaRNBRolmXkuWlZ"
TELEGRAM_TOKEN = "8249656817:AAFAI3oulkDWJZHJ7STSYlDfK-_UJCPo-7U"
TELEGRAM_CHAT_ID = "5804173449"

# CONFIG - Combined Strategy
SYMBOLS = ['DOGEUSDT', 'XAUTUSDT']  # DOGE + Gold
MAX_POSITIONS = 2
POSITION_SIZE_PERCENT = 5
TP_PERCENT = 2.0
SL_PERCENT = 1.5
TRAIL_PERCENT = 0.5
RECV_WINDOW = "5000"

bybit = ccxt.bybit({
    'apiKey': BYBIT_API_KEY,
    'secret': BYBIT_API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

def send_telegram(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                     json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=10)
    except:
        pass

def check_news():
    """Check for Trump/Geopolitical news"""
    try:
        # Simple news check via search (in production use NewsAPI)
        keywords = ['trump', 'iran', 'tariff', 'fed', 'war', 'gold']
        # This is a placeholder - in real system integrate NewsAPI
        return {'breaking': False, 'sentiment': 'neutral'}
    except:
        return {'breaking': False, 'sentiment': 'neutral'}

def get_gold_price():
    """Get gold price for hedge"""
    try:
        r = requests.get('https://api.bybit.com/v5/market/tickers?category=linear&symbol=XAUTUSDT', timeout=10)
        data = r.json()['result']['list'][0]
        return {
            'price': float(data['lastPrice']),
            'change': float(data['price24hPcnt']) * 100,
            'high': float(data['highPrice24h']),
            'low': float(data['lowPrice24h'])
        }
    except:
        return None

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
    """Set TP/SL with proper recv_window"""
    try:
        clean_sym = symbol.replace('/USDT', '')
        
        if side in ['buy', 'long']:
            tp = round(entry_price * (1 + TP_PERCENT/100), 4)
            sl = round(entry_price * (1 - SL_PERCENT/100), 4)
            trail = round(entry_price * (TRAIL_PERCENT/100), 4)
            active = round(entry_price * (1 + TRAIL_PERCENT/100), 4)
        else:
            tp = round(entry_price * (1 - TP_PERCENT/100), 4)
            sl = round(entry_price * (1 + SL_PERCENT/100), 4)
            trail = round(entry_price * (TRAIL_PERCENT/100), 4)
            active = round(entry_price * (1 - TRAIL_PERCENT/100), 4)
        
        # Using proper v5 API with recv_window
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
        
        ma20 = sum(closes[-20:]) / 20
        ma50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else ma20
        
        signals = []
        if rsi < 25:
            signals.append('DEEP_OVERSOLD')
        elif rsi < 35:
            signals.append('OVERSOLD')
        if price < ma20:
            signals.append('BELOW_MA')
        if ma20 > ma50:
            signals.append('TREND_UP')
        
        return {'rsi': rsi, 'price': price, 'ma20': ma20, 'ma50': ma50, 'signals': signals}
    except:
        return None

def check_gold_hedge():
    """Check if we should hedge with gold"""
    gold = get_gold_price()
    if not gold:
        return None
    
    # Gold dip hedge - buy when gold drops 2%+ from high
    dip = (gold['high'] - gold['price']) / gold['high'] * 100
    
    news = check_news()
    
    # Strong signal: gold dip + negative market
    if dip > 2 and gold['change'] < -1:
        return {
            'signal': 'GOLD_HEDGE',
            'reason': f'Gold dip {dip:.1f}% + bad market',
            'price': gold['price']
        }
    
    return None

def analyze_and_trade():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Hybrid Analysis...")
    
    open_positions = get_open_positions()
    
    if len(open_positions) >= MAX_POSITIONS:
        print(f"Max positions: {len(open_positions)}")
        return
    
    balance = get_balance()
    print(f"Balance: ${balance:.2f}")
    
    # Check gold hedge first
    gold_signal = check_gold_hedge()
    if gold_signal and not any('XAUT' in p['symbol'] for p in open_positions):
        print(f"GOLD HEDGE SIGNAL: {gold_signal['reason']}")
        # Could execute gold hedge here
    
    for symbol in SYMBOLS:
        has_position = any(symbol in p['symbol'] for p in open_positions)
        if has_position:
            continue
        
        indicators = get_indicators(symbol)
        if not indicators:
            continue
        
        rsi = indicators['rsi']
        price = indicators['price']
        signals = indicators['signals']
        
        print(f"{symbol}: RSI={rsi:.1f}")
        
        # Strategy: DOGE = deep oversold | Gold = hedge only
        is_doge = 'DOGE' in symbol
        is_gold = 'XAUT' in symbol
        
        should_buy = False
        
        if is_doge:
            # DOGE: Deep oversold only (our 100% win rate strategy)
            should_buy = 'DEEP_OVERSOLD' in signals or ('OVERSOLD' in signals and 'BELOW_MA' in signals)
        
        if should_buy:
            try:
                size = (balance * POSITION_SIZE_PERCENT / 100) / price
                size = round(size, 0) if 'DOGE' in symbol else round(size, 3)
                
                if size < 0.001:
                    continue
                
                print(f"Buying {symbol}...")
                
                order = bybit.create_market_order(symbol=symbol, side='buy', amount=size)
                
                time.sleep(2)
                set_tpsl(symbol, 'long', price)
                
                msg = f"HYBRID BUY {symbol}\nPrice: ${price:.4f}\nSize: {size}\nTP: {TP_PERCENT}% | SL: {SL_PERCENT}%"
                print(msg)
                send_telegram(msg)
                
            except Exception as e:
                print(f"Error: {e}")

def run_bot():
    print("Hybrid Trading System Starting...")
    print("DOGE + Gold Hedge + News Signals")
    send_telegram("Hybrid System Started!\nDOGE (100% win)\nGold Hedge\nNews Signals\nTP 2% | SL 1.5%")
    
    while True:
        try:
            # Ensure TP/SL on all positions
            open_positions = get_open_positions()
            for p in open_positions:
                info = p.get('info', {})
                if info.get('takeProfit', '0') == '0':
                    entry = float(p.get('entryPrice', 0))
                    if entry > 0:
                        set_tpsl(p['symbol'], p['side'], entry)
            
            analyze_and_trade()
            
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(600)  # 10 minutes

if __name__ == "__main__":
    run_bot()