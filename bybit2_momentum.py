"""
AGENT BYBIT2 - Momentum Trading Bot
Second Bybit account with $100 balance
"""

import ccxt
import pandas as pd
import numpy as np
import talib
import time
import json
from datetime import datetime
import os
import sys
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============ CONFIGURATION - $100 Account ============
CONFIG = {
    'symbols': [
        # ONLY WINNERS
        'ETH/USDT:USDT', 'NEAR/USDT:USDT'
    ],
    'timeframe': '5m',
    'lookback': 50,
    'leverage': 3,
    'position_size_pct': 0.35, # 35% of balance per trade (auto-scales)
    'max_positions': 2,       # Max 2 positions
    
    # EMA
    'ema_fast': 9,
    'ema_slow': 21,
    
    # RSI
    'rsi_period': 14,
    'rsi_long': 55,
    'rsi_short': 45,
    
    # TP/SL
    'take_profit_pct': 1.0,
    'stop_loss_pct': 0.5,
    
    'api_key': 'aLz3ySrF9kMZubmqDR',
    'api_secret': '8SlpKyX7vleDu1loJiFePGWfnynJRXZXaD2z',
}

TELEGRAM_TOKEN = "8586893914:AAEIuNFlGNbhDeUQ-eXUOmTm0KHw_-aOtuI"
TELEGRAM_CHAT = "5804173449"

def send_alert(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT, "text": f"🤖 BYBIT2: {message}", "parse_mode": "HTML"}
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[BYBIT2-MOM] {timestamp} - {msg}")

def connect_exchange():
    exchange = ccxt.bybit({
        'apiKey': CONFIG['api_key'],
        'secret': CONFIG['api_secret'],
        'enableRateLimit': True,
        'options': {'defaultType': 'linear', 'adjustForTimeDifference': True}
    })
    exchange.set_sandbox_mode(False)
    return exchange

def get_positions(exchange):
    try:
        positions = exchange.fetch_positions()
        return [p for p in positions if float(p.get('contracts', 0) or 0) != 0]
    except:
        return []

def get_ohlcv(exchange, symbol, timeframe, limit=50):
    try:
        data = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        return pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    except:
        return None

def calculate_signals(df):
    close = df['close'].values
    volume = df['volume'].values
    
    ema_fast = talib.EMA(close, timeperiod=CONFIG['ema_fast'])
    ema_slow = talib.EMA(close, timeperiod=CONFIG['ema_slow'])
    rsi = talib.RSI(close, timeperiod=CONFIG['rsi_period'])
    
    current_close = close[-1]
    current_vol = volume[-1]
    avg_vol = np.mean(volume[-10:])
    
    long_signal = (ema_fast[-1] > ema_slow[-1] and 
                   ema_fast[-2] <= ema_slow[-2] and 
                   rsi[-1] > CONFIG['rsi_long'] and
                   current_vol > avg_vol * 1.2)
    
    # Momentum-only long bias for Bybit2 (short entries disabled per Feb 15 directive)
    short_signal = False
    
    return {'long': long_signal, 'short': short_signal, 'close': current_close}

def adjust_amount(amount, symbol, exchange):
    try:
        market = exchange.market(symbol)
        precision = market['precision']['amount']
        min_amount = market['limits']['amount']['min'] or 0.001
        return max(round(amount, precision), min_amount)
    except:
        return max(round(amount, 3), 0.001)

def open_position(exchange, symbol, side, size):
    try:
        side_ccxt = 'buy' if side == 'long' else 'sell'
        order = exchange.create_order(symbol, 'market', side_ccxt, size)
        log(f"✅ Opened {side.upper()} {size} {symbol}")
        send_alert(f"📈 BYBIT2 Momentum {side.upper()} {symbol}")
        return order
    except Exception as e:
        log(f"❌ Failed: {e}")
        return None

def set_tp_sl(exchange, symbol, side, entry):
    try:
        if side == 'long':
            tp = entry * 1.04
            sl = entry * 0.98
        else:
            tp = entry * 0.96
            sl = entry * 1.02
        
        exchange.set_trading_stop(symbol=symbol, takeProfit=tp)
        exchange.set_trading_stop(symbol=symbol, stopLoss=sl)
        log(f"  TP: {tp:.4f}, SL: {sl:.4f}")
    except Exception as e:
        log(f"  TP/SL error: {e}")

def trading_loop():
    log("="*60)
    log("AGENT BYBIT2 - Momentum Bot Starting")
    log("="*60)
    send_alert("🚀 BYBIT2 Momentum Bot Started")
    
    exchange = connect_exchange()
    last_check = {s: 0 for s in CONFIG['symbols']}
    
    while True:
        try:
            positions = get_positions(exchange)
            available = CONFIG['max_positions'] - len(positions)
            
            # Get balance for position sizing
            try:
                balance = exchange.fetch_balance({'type': 'unified'})
                total_balance = float(balance.get('USDT', {}).get('total', 100))
            except:
                total_balance = 100
            current_syms = [p['symbol'] for p in positions]
            
            log(f"Positions: {len(positions)}/{CONFIG['max_positions']}")
            
            for symbol in CONFIG['symbols']:
                if symbol in current_syms or available <= 0:
                    continue
                
                now = time.time()
                if now - last_check[symbol] < 10:
                    continue
                last_check[symbol] = now
                
                df = get_ohlcv(exchange, symbol, CONFIG['timeframe'])
                if df is None or len(df) < 30:
                    continue
                
                signals = calculate_signals(df)
                
                if signals['long'] or signals['short']:
                    side = 'long' if signals['long'] else 'short'
                    position_value = total_balance * CONFIG['position_size_pct']
                    size = adjust_amount(position_value / signals['close'], symbol, exchange)
                    
                    log(f"🎯 {symbol} {side.upper()} momentum signal!")
                    order = open_position(exchange, symbol, side, size)
                    if order:
                        set_tp_sl(exchange, symbol, side, float(order.get('average', signals['close'])))
                        available -= 1
            
            time.sleep(30)
        except Exception as e:
            log(f"Error: {e}")
            time.sleep(60)

if __name__ == '__main__':
    trading_loop()
