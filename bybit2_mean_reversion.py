"""
AGENT BYBIT2 - Mean Reversion Trading Bot
Second Bybit account with $100 balance - smaller position sizing
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
    'max_positions': 3,       # Max 3 positions = $36 exposure
    
    # Bollinger Bands
    'bb_period': 20,
    'bb_std': 2.0,
    
    # RSI
    'rsi_period': 14,
    'rsi_oversold': 35,
    'rsi_overbought': 65,
    
    # TP/SL
    'take_profit_pct': 1.0,
    'stop_loss_pct': 0.5,
    
    # Bybit2 API Credentials
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
    print(f"[BYBIT2-MR] {timestamp} - {msg}")

def connect_exchange():
    exchange = ccxt.bybit({
        'apiKey': CONFIG['api_key'],
        'secret': CONFIG['api_secret'],
        'enableRateLimit': True,
        'options': {'defaultType': 'linear', 'adjustForTimeDifference': True}
    })
    exchange.set_sandbox_mode(False)
    return exchange

def get_balance(exchange):
    try:
        balance = exchange.fetch_balance({'type': 'unified'})
        usdt = balance.get('USDT', {})
        return float(usdt.get('total', 0)), float(usdt.get('free', 0))
    except Exception as e:
        log(f"Balance error: {e}")
        return 0, 0

def get_positions(exchange):
    try:
        positions = exchange.fetch_positions()
        active = []
        for pos in positions:
            size = float(pos.get('contracts', 0) or 0)
            if size != 0:
                active.append({
                    'symbol': pos['symbol'],
                    'side': pos['side'],
                    'size': size,
                    'entry': float(pos.get('entryPrice', 0) or 0),
                    'mark': float(pos.get('markPrice', 0) or 0),
                    'pnl': float(pos.get('unrealizedPnl', 0) or 0)
                })
        return active
    except Exception as e:
        log(f"Positions error: {e}")
        return []

def get_ohlcv(exchange, symbol, timeframe, limit=50):
    try:
        data = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df
    except Exception as e:
        log(f"OHLCV error for {symbol}: {e}")
        return None

def calculate_signals(df):
    close = df['close'].values
    
    # Bollinger Bands
    upper, middle, lower = talib.BBANDS(close, timeperiod=CONFIG['bb_period'], 
                                         nbdevup=CONFIG['bb_std'], nbdevdn=CONFIG['bb_std'])
    
    # RSI
    rsi = talib.RSI(close, timeperiod=CONFIG['rsi_period'])
    
    # Current values
    current_close = close[-1]
    current_rsi = rsi[-1]
    current_lower = lower[-1]
    current_upper = upper[-1]
    current_middle = middle[-1]
    
    # Signals
    long_signal = current_close <= current_lower and current_rsi < CONFIG['rsi_oversold']
    short_signal = current_close >= current_upper and current_rsi > CONFIG['rsi_overbought']
    
    return {
        'long': long_signal,
        'short': short_signal,
        'close': current_close,
        'rsi': current_rsi,
        'bb_lower': current_lower,
        'bb_upper': current_upper,
        'bb_middle': current_middle
    }

def get_min_amount(exchange, symbol):
    try:
        market = exchange.market(symbol)
        return market['limits']['amount']['min'] or 0.001
    except:
        return 0.001

def adjust_amount(amount, symbol, exchange):
    try:
        market = exchange.market(symbol)
        precision = market['precision']['amount']
        min_amount = market['limits']['amount']['min'] or 0.001
        adjusted = round(amount, precision)
        return max(adjusted, min_amount)
    except:
        return max(round(amount, 3), 0.001)

def open_position(exchange, symbol, side, size):
    try:
        order_type = 'market'
        side_ccxt = 'buy' if side == 'long' else 'sell'
        
        order = exchange.create_order(
            symbol=symbol,
            type=order_type,
            side=side_ccxt,
            amount=size
        )
        
        log(f"✅ Opened {side.upper()} {size} {symbol}")
        send_alert(f"📈 BYBIT2 Opened {side.upper()} {symbol}\nSize: {size}")
        return order
    except Exception as e:
        log(f"❌ Failed to open position: {e}")
        return None

def set_tp_sl(exchange, symbol, side, entry_price):
    try:
        tp_pct = CONFIG['take_profit_pct'] / 100
        sl_pct = CONFIG['stop_loss_pct'] / 100
        
        if side == 'long':
            tp_price = entry_price * (1 + tp_pct)
            sl_price = entry_price * (1 - sl_pct)
            trigger_direction = 2
        else:
            tp_price = entry_price * (1 - tp_pct)
            sl_price = entry_price * (1 + sl_pct)
            trigger_direction = 1
        
        # Set TP
        try:
            exchange.set_trading_stop(symbol=symbol, takeProfit=tp_price)
            log(f"  TP set at {tp_price:.4f}")
        except Exception as e:
            log(f"  TP error: {e}")
        
        # Set SL
        try:
            exchange.set_trading_stop(symbol=symbol, stopLoss=sl_price)
            log(f"  SL set at {sl_price:.4f}")
        except Exception as e:
            log(f"  SL error: {e}")
            
    except Exception as e:
        log(f"TP/SL setup error: {e}")

def trading_loop():
    log("="*60)
    log("AGENT BYBIT2 - Mean Reversion Bot Starting")
    log("Account Size: $100 | Position Size: $12 | Max Positions: 3")
    log("="*60)
    
    send_alert("🚀 BYBIT2 Mean Reversion Bot Started\nBalance: $100\nPosition: $12/trade")
    
    exchange = connect_exchange()
    
    # Test connection
    try:
        balance, free = get_balance(exchange)
        log(f"[OK] Connected. Balance: ${balance:.2f} USDT")
    except Exception as e:
        log(f"[FAIL] Connection failed: {e}")
        return
    
    last_check = {symbol: 0 for symbol in CONFIG['symbols']}
    
    while True:
        try:
            # Get current state
            balance, free = get_balance(exchange)
            positions = get_positions(exchange)
            
            current_symbols = [p['symbol'] for p in positions]
            available_slots = CONFIG['max_positions'] - len(positions)
            
            log(f"Balance: ${balance:.2f} | Positions: {len(positions)}/{CONFIG['max_positions']}")
            
            # Check each symbol
            for symbol in CONFIG['symbols']:
                if symbol in current_symbols:
                    continue
                
                if available_slots <= 0:
                    break
                
                # Rate limiting
                now = time.time()
                if now - last_check[symbol] < 10:
                    continue
                last_check[symbol] = now
                
                # Get data and signals
                df = get_ohlcv(exchange, symbol, CONFIG['timeframe'])
                if df is None or len(df) < CONFIG['lookback']:
                    continue
                
                signals = calculate_signals(df)
                
                # Check for entry
                if signals['long'] or signals['short']:
                    side = 'long' if signals['long'] else 'short'
                    
                    # Calculate position size from percentage of balance
                    current_price = signals['close']
                    position_value = balance * CONFIG['position_size_pct']
                    size = position_value / current_price
                    size = adjust_amount(size, symbol, exchange)
                    
                    log(f"🎯 {symbol} {side.upper()} signal detected!")
                    log(f"   Price: {current_price:.4f} | RSI: {signals['rsi']:.1f}")
                    
                    # Open position
                    order = open_position(exchange, symbol, side, size)
                    if order:
                        entry = float(order['average'] or order['price'] or current_price)
                        set_tp_sl(exchange, symbol, side, entry)
                        available_slots -= 1
            
            # Log positions
            if positions:
                total_pnl = sum(p['pnl'] for p in positions)
                log(f"Total Unrealized P&L: ${total_pnl:.2f}")
            
            time.sleep(30)
            
        except Exception as e:
            log(f"Loop error: {e}")
            time.sleep(60)

if __name__ == '__main__':
    trading_loop()
