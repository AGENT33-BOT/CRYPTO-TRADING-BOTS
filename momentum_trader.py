"""
Momentum Trading Bot for Bybit Futures
Strategy: EMA Crossover + MACD + Volume for trend continuation
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============ CONFIGURATION ============
CONFIG = {
    'symbols': [
        # ONLY WINNERS - Based on trade history
        'ETH/USDT:USDT', 'NEAR/USDT:USDT', 'LINK/USDT:USDT', 'DOGE/USDT:USDT'
        # REMOVED: BTC, SOL, XRP (losing pairs)
    ],
    'timeframe': '5m',           # 5-minute candles
    'lookback': 100,             # Candles to fetch
    'leverage': 3,
    'position_size_pct': 0.05,   # STRICT: 5% max per position
    'max_positions': 2,          # STRICT: Max 2 positions
    'min_confidence': 90,        # STRICT: 90% min confidence
    
    # Strategy params
    'ema_fast': 9,
    'ema_slow': 21,
    'rsi_period': 14,
    'rsi_long_min': 50,          # RSI > 50 for longs
    'rsi_short_max': 50,         # RSI < 50 for shorts
    'volume_threshold': 1.2,     # Volume > 1.2x average
    
    # Risk management - TIGHTENED based on analysis
    'stop_loss_pct': 0.015,      # 1.5% SL (was 2%)
    'take_profit_pct': 0.03,     # 3% TP (take profit faster)
}

LOG_FILE = 'momentum_trader.log'
POSITIONS_FILE = 'momentum_positions.json'

# ============ LOGGING ============
def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')

# ============ EXCHANGE SETUP ============
def get_exchange():
    """Initialize Bybit exchange with proper API credentials"""
    try:
        api_key = 'bsK06QDhsagOWwFsXQ'
        api_secret = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'
        
        if not api_key or not api_secret:
            log("[ERR] API credentials not configured")
            return None
        
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',
                'adjustForTimeDifference': True,
            }
        })
        exchange.set_sandbox_mode(False)
        
        # Test connection
        exchange.load_markets()
        return exchange
        
    except Exception as e:
        log(f"[ERR] Exchange error: {e}")
        return None

def get_symbol_precision(exchange, symbol):
    """Get amount precision for symbol"""
    try:
        market = exchange.market(symbol)
        amount_precision = market.get('precision', {}).get('amount', 3)
        min_amount = market.get('limits', {}).get('amount', {}).get('min', 0.001)
        return amount_precision, min_amount
    except:
        return 3, 0.001

def adjust_amount(amount, precision, min_amount):
    """Adjust amount to meet precision and minimum requirements"""
    amount = round(amount, int(precision))
    amount = max(amount, float(min_amount))
    return amount

# ============ DATA FUNCTIONS ============
def fetch_ohlcv(exchange, symbol, timeframe='5m', limit=100):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        log(f"[ERR] Fetch error {symbol}: {e}")
        return None

def calculate_indicators(df):
    # EMAs
    df['ema_fast'] = talib.EMA(df['close'], timeperiod=CONFIG['ema_fast'])
    df['ema_slow'] = talib.EMA(df['close'], timeperiod=CONFIG['ema_slow'])
    
    # MACD
    df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(
        df['close'], fastperiod=12, slowperiod=26, signalperiod=9
    )
    
    # RSI
    df['rsi'] = talib.RSI(df['close'], timeperiod=CONFIG['rsi_period'])
    
    # Volume
    df['volume_sma'] = df['volume'].rolling(window=20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma']
    
    # ATR
    df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
    
    return df

# ============ SIGNAL GENERATION ============
def generate_signal(df, symbol):
    if len(df) < 50:
        return None
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    
    if pd.isna(current['ema_fast']) or pd.isna(current['rsi']):
        return None
    
    signal = None
    
    # LONG Signal: EMA crossover + momentum
    if (prev['ema_fast'] <= prev['ema_slow'] and 
        current['ema_fast'] > current['ema_slow'] and
        current['rsi'] > CONFIG['rsi_long_min'] and
        current['volume_ratio'] > CONFIG['volume_threshold'] and
        current['macd'] > current['macd_signal']):
        
        confidence = 70
        
        if current['rsi'] > 60:
            confidence += 10
        if current['volume_ratio'] > 1.5:
            confidence += 10
        if current['macd_hist'] > 0 and prev['macd_hist'] <= 0:
            confidence += 5
        
        signal = {
            'symbol': symbol,
            'side': 'LONG',
            'confidence': min(95, confidence),
            'entry_price': current['close'],
            'rsi': current['rsi'],
            'reason': f"EMA crossover + momentum ({current['rsi']:.1f} RSI)"
        }
    
    # SHORT Signal: EMA crossunder + momentum
    elif (prev['ema_fast'] >= prev['ema_slow'] and 
          current['ema_fast'] < current['ema_slow'] and
          current['rsi'] < CONFIG['rsi_short_max'] and
          current['volume_ratio'] > CONFIG['volume_threshold'] and
          current['macd'] < current['macd_signal']):
        
        confidence = 70
        
        if current['rsi'] < 40:
            confidence += 10
        if current['volume_ratio'] > 1.5:
            confidence += 10
        if current['macd_hist'] < 0 and prev['macd_hist'] >= 0:
            confidence += 5
        
        signal = {
            'symbol': symbol,
            'side': 'SHORT',
            'confidence': min(95, confidence),
            'entry_price': current['close'],
            'rsi': current['rsi'],
            'reason': f"EMA crossunder + momentum ({current['rsi']:.1f} RSI)"
        }
    
    if signal and signal['confidence'] >= CONFIG['min_confidence']:
        if signal['side'] == 'LONG':
            signal['stop_loss'] = current['close'] * (1 - CONFIG['stop_loss_pct'])
            signal['take_profit'] = current['close'] * (1 + CONFIG['take_profit_pct'])
        else:
            signal['stop_loss'] = current['close'] * (1 + CONFIG['stop_loss_pct'])
            signal['take_profit'] = current['close'] * (1 - CONFIG['take_profit_pct'])
        
        # Round prices
        signal['stop_loss'] = round(signal['stop_loss'], 2)
        signal['take_profit'] = round(signal['take_profit'], 2)
        
        return signal
    
    return None

# ============ POSITION MANAGEMENT ============
def load_positions():
    try:
        if os.path.exists(POSITIONS_FILE):
            with open(POSITIONS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        log(f"[WARN] Load error: {e}")
    return {}

def save_positions(positions):
    try:
        with open(POSITIONS_FILE, 'w') as f:
            json.dump(positions, f, indent=2, default=str)
    except Exception as e:
        log(f"[WARN] Save error: {e}")

def get_position_count():
    return len(load_positions())

# ============ TRADING FUNCTIONS ============
def open_position(exchange, signal):
    """Open a new position with proper TP/SL protection"""
    try:
        symbol = signal['symbol']
        side = signal['side']
        
        positions = load_positions()
        if symbol in positions:
            log(f"[SKIP] Position exists in {symbol}")
            return False
        
        # Get symbol precision
        amount_precision, min_amount = get_symbol_precision(exchange, symbol)
        
        try:
            exchange.set_leverage(CONFIG['leverage'], symbol)
        except:
            pass
        
        # Calculate position size from percentage of balance
        balance = exchange.fetch_balance()
        total_balance = float(balance.get('USDT', {}).get('total', 0))
        position_value = total_balance * CONFIG['position_size_pct']
        raw_amount = position_value / signal['entry_price']
        amount = adjust_amount(raw_amount, amount_precision, min_amount)
        
        order_side = 'buy' if side == 'LONG' else 'sell'
        
        order = exchange.create_order(
            symbol=symbol,
            type='market',
            side=order_side,
            amount=amount,
            params={'leverage': CONFIG['leverage']}
        )
        
        # SL/TP orders
        sl_side = 'sell' if side == 'LONG' else 'buy'
        
        # triggerDirection: 2 = trigger when price falls to stopPrice (for LONG SL)
        # triggerDirection: 1 = trigger when price rises to stopPrice (for SHORT SL)
        trigger_direction = 2 if side == 'LONG' else 1
        
        sl_order = exchange.create_order(
            symbol=symbol,
            type='stop',
            side=sl_side,
            amount=amount,
            params={
                'stopPrice': signal['stop_loss'],
                'triggerDirection': trigger_direction,
                'reduceOnly': True
            }
        )
        
        tp_order = exchange.create_order(
            symbol=symbol,
            type='limit',
            side=sl_side,
            amount=amount,
            price=signal['take_profit'],
            params={'reduceOnly': True}
        )
        
        positions[symbol] = {
            'side': side,
            'entry_price': signal['entry_price'],
            'amount': amount,
            'stop_loss': signal['stop_loss'],
            'take_profit': signal['take_profit'],
            'confidence': signal['confidence'],
            'entry_time': datetime.now().isoformat(),
            'order_id': order['id'],
            'sl_order_id': sl_order['id'],
            'tp_order_id': tp_order['id']
        }
        save_positions(positions)
        
        log(f"[OK] {side} {symbol} @ ${signal['entry_price']:.4f} ({signal['confidence']:.0f}%)")
        log(f"   SL: ${signal['stop_loss']:.4f} | TP: ${signal['take_profit']:.4f}")
        return True
        
    except Exception as e:
        log(f"[ERR] Open error: {e}")
        import traceback
        log(f"[ERR] Traceback: {traceback.format_exc()}")
        return False

def check_positions(exchange):
    try:
        positions = load_positions()
        if not positions:
            return
        
        try:
            exchange_positions = exchange.fetch_positions()
            exchange_symbols = {p['symbol'] for p in exchange_positions if p['contracts'] and float(p['contracts']) != 0}
        except:
            exchange_symbols = set()
        
        for symbol in list(positions.keys()):
            if symbol not in exchange_symbols:
                log(f"[CLEAN] {symbol} closed, removing")
                del positions[symbol]
        
        save_positions(positions)
    except Exception as e:
        log(f"[WARN] Check error: {e}")

# ============ MAIN LOOP ============
def scan_markets():
    exchange = get_exchange()
    if not exchange:
        return []
    
    log("[SCAN] Scanning for Momentum signals...")
    signals = []
    
    for symbol in CONFIG['symbols']:
        try:
            df = fetch_ohlcv(exchange, symbol, CONFIG['timeframe'], CONFIG['lookback'])
            if df is None:
                continue
            
            df = calculate_indicators(df)
            signal = generate_signal(df, symbol)
            
            if signal:
                signals.append(signal)
                log(f"[SIG] {symbol}: {signal['side']} ({signal['confidence']:.0f}%)")
        except Exception as e:
            pass
    
    return signals

def main_loop():
    log("=" * 70)
    log("[START] Momentum Trader Started")
    log("=" * 70)
    
    while True:
        try:
            exchange = get_exchange()
            if exchange:
                check_positions(exchange)
            
            if get_position_count() < CONFIG['max_positions']:
                signals = scan_markets()
                
                if signals:
                    signals.sort(key=lambda x: x['confidence'], reverse=True)
                    
                    for signal in signals:
                        if signal['confidence'] >= CONFIG['min_confidence']:
                            if get_position_count() < CONFIG['max_positions']:
                                open_position(exchange, signal)
            else:
                log(f"[WAIT] Max positions ({CONFIG['max_positions']}) reached")
            
            log(f"[SLEEP] Sleep 60s... (Positions: {get_position_count()})")
            time.sleep(60)
            
        except Exception as e:
            log(f"[ERR] Loop error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        log("[STOP] Stopped")
