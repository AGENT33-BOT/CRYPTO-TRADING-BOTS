"""
AI Trading Bot - Full Autonomous Trading
Simplified version that actually works
"""

import ccxt
import time
import requests
from datetime import datetime
from threading import Thread

# Config
BYBIT_API_KEY = "KfmiIdWd16hG18v2O7"
BYBIT_SECRET = "VTVePZIz2GEqyy6AcvwPVcaRNBRolmXkuWlZ"
TELEGRAM_TOKEN = "8249656817:AAFAI3oulkDWJZHJ7STSYlDfK-_UJCPo-7U"
TELEGRAM_CHAT_ID = "5804173449"

# Trading pairs
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'NEARUSDT', 'LINKUSDT', 'DOGEUSDT']

# Settings
MAX_POSITIONS = 3
POSITION_SIZE_PERCENT = 10
TP_PERCENT = 2.5
SL_PERCENT = 2.5

# Initialize exchange
bybit = ccxt.bybit({
    'apiKey': BYBIT_API_KEY,
    'secret': BYBIT_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

def send_telegram(message):
    """Send Telegram message"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data, timeout=10)
    except:
        pass

def get_balance():
    """Get account balance"""
    try:
        balance = bybit.fetch_balance()
        return balance['USDT']['total']
    except:
        return 0

def get_open_positions():
    """Get open positions"""
    try:
        positions = bybit.fetch_positions()
        return [p for p in positions if float(p.get('contracts', 0)) > 0]
    except:
        return []

def get_indicators(symbol):
    """Get technical indicators"""
    try:
        # Get candles
        ohlcv = bybit.fetch_ohlcv(symbol, '15m', limit=50)
        closes = [c[4] for c in ohlcv]
        
        if len(closes) < 20:
            return None
        
        # RSI
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        avg_gain = sum(gains[-14:]) / 14
        avg_loss = sum(losses[-14:]) / 14
        rs = avg_gain / (avg_loss + 0.0001)
        rsi = 100 - (100 / (1 + rs))
        
        # MA
        ma20 = sum(closes[-20:]) / 20
        ma50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else ma20
        
        # Price vs MA
        price = closes[-1]
        
        # Simple signals
        signals = []
        
        # RSI signal
        if rsi < 30:
            signals.append('RSI_OVERSOLD')
        elif rsi > 70:
            signals.append('RSI_OVERBOUGHT')
        
        # MA signal
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
    except Exception as e:
        return None

def analyze_and_trade():
    """Main trading logic"""
    print("Analyzing market...")
    
    # Get open positions
    open_positions = get_open_positions()
    
    if len(open_positions) >= MAX_POSITIONS:
        print(f"Max positions reached: {len(open_positions)}")
        return
    
    balance = get_balance()
    print(f"Balance: ${balance:.2f}")
    
    for symbol in SYMBOLS:
        # Skip if already have position
        has_position = any(symbol in p['symbol'] for p in open_positions)
        if has_position:
            continue
        
        # Get indicators
        indicators = get_indicators(symbol)
        if not indicators:
            continue
        
        signals = indicators['signals']
        rsi = indicators['rsi']
        
        print(f"{symbol}: RSI={rsi:.1f} Signals={signals}")
        
        # Trading logic
        should_buy = (
            'RSI_OVERSOLD' in signals or 
            ('ABOVE_MA20' in signals and 'TREND_UP' in signals)
        )
        
        should_sell = 'RSI_OVERBOUGHT' in signals
        
        if should_buy:
            try:
                # Calculate size
                size = (balance * POSITION_SIZE_PERCENT / 100) / indicators['price']
                size = round(size, 3)
                
                if size < 0.001:
                    continue
                
                print(f"Buying {symbol}...")
                
                # Place order
                order = bybit.create_market_order(
                    symbol=symbol,
                    side='buy',
                    amount=size
                )
                
                # Set TP/SL
                tp_price = indicators['price'] * (1 + TP_PERCENT / 100)
                sl_price = indicators['price'] * (1 - SL_PERCENT / 100)
                
                try:
                    bybit.set_leverage(10, symbol)
                except:
                    pass
                
                # Set stop loss
                try:
                    bybit.set_stop_loss(symbol, sl_price)
                except:
                    pass
                
                # Take profit order
                try:
                    bybit.set_take_profit(symbol, tp_price)
                except:
                    pass
                
                msg = f"✅ BUY {symbol}\nPrice: ${indicators['price']:.4f}\nSize: {size}\nTP: {TP_PERCENT}% | SL: {SL_PERCENT}%"
                print(msg)
                send_telegram(msg)
                
            except Exception as e:
                print(f"Error buying {symbol}: {e}")
        
        time.sleep(1)

def send_hourly_report():
    """Send hourly report"""
    balance = get_balance()
    positions = get_open_positions()
    
    pos_text = ""
    for p in positions:
        sym = p['symbol']
        side = p['side']
        pnl = float(p.get('unrealizedPnl', 0))
        pos_text += f"\n{sym} {side}: ${pnl:.2f}"
    
    if not pos_text:
        pos_text = "\nNo open positions"
    
    msg = f"""
🤖 AI Trading Report

Balance: ${balance:.2f}
Open Positions: {len(positions)}{pos_text}

AI System: Running
"""
    send_telegram(msg)

def run_bot():
    """Main bot loop"""
    print("Starting AI Trading Bot...")
    send_telegram("🤖 AI Trading Bot Started!")
    
    last_report = time.time()
    
    while True:
        try:
            analyze_and_trade()
            
            # Hourly report
            if time.time() - last_report >= 3600:
                send_hourly_report()
                last_report = time.time()
            
            # Wait 5 minutes
            time.sleep(300)
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_bot()
