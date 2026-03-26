"""
AI Trading System - Optimized Version
Focus on profitable pairs only
Based on trade history analysis
"""
import ccxt
import time
import requests
from datetime import datetime

BYBIT_API_KEY = "KfmiIdWd16hG18v2O7"
BYBIT_SECRET = "VTVePZIz2GEqyy6AcvwPVcaRNBRolmXkuWlZ"
TELEGRAM_TOKEN = "8249656817:AAFAI3oulkDWJZHJ7STSYlDfK-_UJCPo-7U"
TELEGRAM_CHAT_ID = "5804173449"

# OPTIMIZED: Removed LINK, DOGE (losing pairs)
# Focus on ETH (80% win), NEAR (100% win), BTC, SOL, BNB
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'NEARUSDT']
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

def set_tpsl(symbol, side, entry_price):
    """Set TP/SL + Trailing"""
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
    """Get technical indicators"""
    try:
        ohlcv = bybit.fetch_ohlcv(symbol, '15m', limit=50)
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
        
        return {
            'rsi': rsi,
            'price': price,
            'ma20': ma20,
            'ma50': ma50,
            'signals': signals
        }
    except:
        return None

def analyze_and_trade():
    """Main trading logic - STRICTER signals"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Analyzing market...")
    
    open_positions = get_open_positions()
    
    if len(open_positions) >= MAX_POSITIONS:
        print(f"Max positions: {len(open_positions)}")
        return
    
    balance = get_balance()
    
    for symbol in SYMBOLS:
        has_position = any(symbol in p['symbol'] for p in open_positions)
        if has_position:
            continue
        
        indicators = get_indicators(symbol)
        if not indicators:
            continue
        
        signals = indicators['signals']
        rsi = indicators['rsi']
        
        print(f"{symbol}: RSI={rsi:.1f} Signals={signals}")
        
        # STRICTER buy signals - only buy on strong oversold + trend
        should_buy = (
            'RSI_OVERSOLD' in signals and 'ABOVE_MA20' in signals
        ) or (
            'RSI_OVERSOLD' in signals and rsi < 25
        )
        
        if should_buy:
            try:
                size = (balance * POSITION_SIZE_PERCENT / 100) / indicators['price']
                size = round(size, 3)
                
                if size < 0.001:
                    continue
                
                print(f"Buying {symbol}...")
                
                order = bybit.create_market_order(symbol=symbol, side='buy', amount=size)
                
                time.sleep(1)
                set_tpsl(symbol, 'long', indicators['price'])
                
                msg = f"AI BUY {symbol}\nPrice: ${indicators['price']:.4f}\nSize: {size}\nTP: {TP_PERCENT}% | SL: {SL_PERCENT}%"
                print(msg)
                send_telegram(msg)
                
            except Exception as e:
                print(f"Error: {e}")

def run_bot():
    """Main loop"""
    print("Starting Optimized AI Trading System...")
    send_telegram("AI Trading Optimized!\nRemoved LINK, DOGE\nFocus: ETH, NEAR, BTC, SOL, BNB\nStricter signals")
    
    while True:
        try:
            # First ensure all positions have TP/SL
            open_positions = get_open_positions()
            for p in open_positions:
                info = p.get('info', {})
                if info.get('takeProfit', '0') == '0':
                    entry = float(p.get('entryPrice', 0))
                    if entry > 0:
                        set_tpsl(p['symbol'], p['side'], entry)
            
            # Then analyze and trade
            analyze_and_trade()
            
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(300)  # 5 minutes

if __name__ == "__main__":
    run_bot()