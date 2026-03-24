"""
Scalping Bot for Bybit Futures
Strategy: Quick 0.5-1% moves using 1-minute RSI + Price action
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
        'ETH/USDT:USDT', 'NEAR/USDT:USDT'
        # REMOVED: BTC, SOL, DOGE, XRP (losing pairs)
    ],
    'timeframe': '1m',           # 1-minute candles for scalping
    'lookback': 50,
    'leverage': 5,               # Higher leverage for scalping
    'position_size_pct': 0.08,   # 8% of available balance per trade (auto-scales)
    'max_positions': 3,
    'min_confidence': 80,        # Higher confidence for scalping
    
    # POSITION SIZING RULES - From analysis Feb 23, 2026
    'max_position_pct': 0.20,    # Max 20% of account per position (increased for larger balance)
    'max_symbol_pct': 0.25,      # Max 25% per symbol
    'min_free_balance': 10,      # Minimum $10 free balance required
    'high_vol_symbols': ['NEAR/USDT:USDT'],  # Reduce size 30% for these
    'high_vol_reduction': 0.30,  # 30% reduction for high volatility
    
    # Strategy params
    'rsi_period': 7,             # Faster RSI
    'rsi_oversold': 30,
    'rsi_overbought': 70,
    'profit_target': 0.008,      # 0.8% profit
    'stop_loss': 0.005,          # 0.5% stop
    'max_hold_minutes': 15,      # Exit after 15 min max
}

LOG_FILE = 'scalping_bot.log'
POSITIONS_FILE = 'scalping_positions.json'

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')

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

def fetch_ohlcv(exchange, symbol, timeframe='1m', limit=50):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        return None

def calculate_indicators(df):
    df['rsi'] = talib.RSI(df['close'], timeperiod=CONFIG['rsi_period'])
    df['ema_9'] = talib.EMA(df['close'], timeperiod=9)
    df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=7)
    
    # Price change
    df['price_change_3'] = df['close'].pct_change(3) * 100
    df['price_change_5'] = df['close'].pct_change(5) * 100
    
    return df

def generate_signal(df, symbol):
    if len(df) < 20:
        return None
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    
    if pd.isna(current['rsi']):
        return None
    
    signal = None
    
    # LONG: RSI oversold bounce with price stabilization
    if (current['rsi'] < CONFIG['rsi_oversold'] and
        prev['rsi'] < current['rsi'] and
        current['close'] > current['ema_9'] * 0.998):
        
        confidence = 75 + (CONFIG['rsi_oversold'] - current['rsi'])
        
        signal = {
            'symbol': symbol,
            'side': 'LONG',
            'confidence': min(95, confidence),
            'entry_price': current['close'],
            'entry_time': datetime.now(),
            'reason': f"RSI oversold bounce ({current['rsi']:.1f})"
        }
    
    # SHORT: RSI overbought pullback
    elif (current['rsi'] > CONFIG['rsi_overbought'] and
          prev['rsi'] > current['rsi'] and
          current['close'] < current['ema_9'] * 1.002):
        
        confidence = 75 + (current['rsi'] - CONFIG['rsi_overbought'])
        
        signal = {
            'symbol': symbol,
            'side': 'SHORT',
            'confidence': min(95, confidence),
            'entry_price': current['close'],
            'entry_time': datetime.now(),
            'reason': f"RSI overbought pullback ({current['rsi']:.1f})"
        }
    
    if signal and signal['confidence'] >= CONFIG['min_confidence']:
        if signal['side'] == 'LONG':
            signal['stop_loss'] = signal['entry_price'] * (1 - CONFIG['stop_loss'])
            signal['take_profit'] = signal['entry_price'] * (1 + CONFIG['profit_target'])
        else:
            signal['stop_loss'] = signal['entry_price'] * (1 + CONFIG['stop_loss'])
            signal['take_profit'] = signal['entry_price'] * (1 - CONFIG['profit_target'])
        
        # Round prices
        signal['stop_loss'] = round(signal['stop_loss'], 2)
        signal['take_profit'] = round(signal['take_profit'], 2)
        
        return signal
    
    return None

def load_positions():
    try:
        if os.path.exists(POSITIONS_FILE):
            with open(POSITIONS_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_positions(positions):
    try:
        with open(POSITIONS_FILE, 'w') as f:
            json.dump(positions, f, indent=2, default=str)
    except:
        pass

def get_position_count():
    return len(load_positions())

def validate_position_sizing(exchange, symbol, side, entry_price):
    """
    Validate position sizing against risk rules.
    Returns: (is_valid, adjusted_size, reason)
    """
    try:
        # Get account balance
        balance = exchange.fetch_balance()
        usdt_balance = float(balance.get('USDT', {}).get('free', 0))
        total_balance = float(balance.get('USDT', {}).get('total', 0))
        
        # Check minimum free balance
        if usdt_balance < CONFIG['min_free_balance']:
            return False, 0, f"Insufficient free balance: ${usdt_balance:.2f} (need ${CONFIG['min_free_balance']})"
        
        # Calculate position value from percentage of balance
        position_value = total_balance * CONFIG['position_size_pct']
        
        # Check max position percentage (15%)
        max_position_value = total_balance * CONFIG['max_position_pct']
        if position_value > max_position_value:
            position_value = max_position_value
            log(f"[RISK] Position size reduced to ${position_value:.2f} (15% limit)")
        
        # Check high volatility symbols (reduce 30%)
        if symbol in CONFIG['high_vol_symbols']:
            position_value = position_value * (1 - CONFIG['high_vol_reduction'])
            log(f"[RISK] {symbol} size reduced 30% for high volatility")
        
        # Check symbol concentration (25% max)
        positions = load_positions()
        symbol_exposure = 0
        for pos_symbol, pos in positions.items():
            if pos_symbol == symbol:
                symbol_exposure += pos['entry_price'] * pos['amount']
        
        max_symbol_value = total_balance * CONFIG['max_symbol_pct']
        available_for_symbol = max_symbol_value - symbol_exposure
        
        if position_value > available_for_symbol:
            position_value = max(0, available_for_symbol)
            if position_value < 5:  # Minimum $5 trade
                return False, 0, f"Symbol {symbol} at max allocation (25%)"
            log(f"[RISK] {symbol} position limited to ${position_value:.2f} (25% symbol limit)")
        
        return True, position_value, "OK"
        
    except Exception as e:
        log(f"[WARN] Sizing validation error: {e}")
        return True, CONFIG['position_size'], "Validation skipped"

def open_position(exchange, signal):
    """Open a new position with proper TP/SL protection and position sizing"""
    try:
        symbol = signal['symbol']
        side = signal['side']
        
        positions = load_positions()
        if symbol in positions:
            return False
        
        # Validate position sizing
        is_valid, position_value, reason = validate_position_sizing(
            exchange, symbol, side, signal['entry_price']
        )
        
        if not is_valid:
            log(f"[SKIP] {symbol}: {reason}")
            return False
        
        # Get symbol precision
        amount_precision, min_amount = get_symbol_precision(exchange, symbol)
        
        try:
            exchange.set_leverage(CONFIG['leverage'], symbol)
        except:
            pass
        
        # Calculate and adjust position size with validated value
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
        
        sl_side = 'sell' if side == 'LONG' else 'buy'
        
        # triggerDirection: 2 = trigger when price falls to stopPrice (for LONG SL)
        # triggerDirection: 1 = trigger when price rises to stopPrice (for SHORT SL)
        trigger_direction = 2 if side == 'LONG' else 1
        
        # FIXED: Use 'stop_market' instead of 'stop' for Bybit
        # FIXED: Correct trigger direction parameter
        sl_params = {
            'stopPrice': signal['stop_loss'],
            'reduceOnly': True,
            'triggerPrice': signal['stop_loss'],
            'triggerDirection': 'falling' if side == 'LONG' else 'rising'
        }
        
        sl_order = exchange.create_order(
            symbol=symbol,
            type='stop_market',
            side=sl_side,
            amount=amount,
            params=sl_params
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
            'entry_time': signal['entry_time'].isoformat(),
            'order_id': order['id'],
            'sl_order_id': sl_order['id'],
            'tp_order_id': tp_order['id']
        }
        save_positions(positions)
        
        log(f"[OK] SCALP {side} {symbol} @ ${signal['entry_price']:.4f}")
        log(f"   SL: ${signal['stop_loss']:.4f} | TP: ${signal['take_profit']:.4f}")
        return True
        
    except Exception as e:
        log(f"[ERR] Open error: {e}")
        import traceback
        log(f"[ERR] Traceback: {traceback.format_exc()}")
        return False

def check_time_based_exits(exchange):
    """Close positions held too long"""
    try:
        positions = load_positions()
        now = datetime.now()
        
        for symbol, pos in list(positions.items()):
            entry_time = datetime.fromisoformat(pos['entry_time'])
            hold_time = (now - entry_time).total_seconds() / 60
            
            if hold_time > CONFIG['max_hold_minutes']:
                try:
                    # Get symbol precision for closing
                    amount_precision, min_amount = get_symbol_precision(exchange, symbol)
                    amount = adjust_amount(pos['amount'], amount_precision, min_amount)
                    
                    close_side = 'sell' if pos['side'] == 'LONG' else 'buy'
                    exchange.create_order(
                        symbol=symbol,
                        type='market',
                        side=close_side,
                        amount=amount,
                        params={'reduceOnly': True}
                    )
                    log(f"[TIME] Time exit {symbol} ({hold_time:.0f} min)")
                    del positions[symbol]
                except Exception as e:
                    log(f"[WARN] Time exit error: {e}")
        
        save_positions(positions)
    except Exception as e:
        log(f"[WARN] Exit check error: {e}")

def main_loop():
    log("=" * 70)
    log("[FAST] Scalping Bot Started (1m timeframe)")
    log(f"Targets: ±{CONFIG['profit_target']*100:.1f}% | Max hold: {CONFIG['max_hold_minutes']} min")
    log("=" * 70)
    
    while True:
        try:
            exchange = get_exchange()
            if exchange:
                check_time_based_exits(exchange)
            
            if get_position_count() < CONFIG['max_positions']:
                log("[SCAN] Scanning for scalp opportunities...")
                
                for symbol in CONFIG['symbols']:
                    try:
                        df = fetch_ohlcv(exchange, symbol, CONFIG['timeframe'], CONFIG['lookback'])
                        if df is None:
                            continue
                        
                        df = calculate_indicators(df)
                        signal = generate_signal(df, symbol)
                        
                        if signal and signal['confidence'] >= CONFIG['min_confidence']:
                            log(f"[SIG] {symbol}: {signal['side']} scalp ({signal['confidence']:.0f}%)")
                            
                            if get_position_count() < CONFIG['max_positions']:
                                open_position(exchange, signal)
                    except Exception as e:
                        pass
            else:
                log(f"[WAIT] Max positions reached")
            
            log(f"[SLEEP] Sleep 30s... (Positions: {get_position_count()})")
            time.sleep(30)
            
        except Exception as e:
            log(f"[ERR] Loop error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        log("[STOP] Stopped")
