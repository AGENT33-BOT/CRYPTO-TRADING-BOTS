"""
Mean Reversion Trading Bot for Bybit Futures
Strategy: Bollinger Bands + RSI for oversold/overbought bounces
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

# Add parent dir for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============ CONFIGURATION ============
CONFIG = {
    'symbols': [
        # ONLY WINNERS - Based on trade history analysis
        'ETH/USDT:USDT', 'NEAR/USDT:USDT'
        # REMOVED: BTC, SOL, DOGE, XRP, ADA, LINK, DOT (losing pairs)
    ],
    'timeframe': '5m',           # 5-minute candles for quick signals
    'lookback': 50,              # Candles to fetch
    'leverage': 3,               # 3x leverage
    'position_size_pct': 0.25,   # 25% of available balance per trade (INCREASED)
    'max_positions': 5,          # Max concurrent positions
    'min_confidence': 75,        # Min confidence to trade
    
    # Strategy params
    'rsi_period': 14,
    'rsi_oversold': 35,          # Long when RSI < 35
    'rsi_overbought': 65,        # Short when RSI > 65
    'bb_period': 20,
    'bb_std': 2,
    'bb_threshold': 0.1,         # BB position threshold (0.1 = near lower/upper)
    
    # Risk management - TIGHTENED based on analysis
    'stop_loss_pct': 0.015,      # 1.5% SL (was 2%)
    'take_profit_pct': 0.03,     # 3% TP (take profit faster)
    'trailing_stop': True,
    'trailing_pct': 0.01,        # 1% trailing (was 1.5%)
    
    # POSITION SIZING RULES - From analysis Feb 23, 2026
    'max_position_pct': 0.40,    # Max 40% of account per position (INCREASED)
    'max_symbol_pct': 0.25,      # Max 25% per symbol
    'min_free_balance': 10,      # Minimum $10 free balance required
    'high_vol_symbols': ['NEAR/USDT:USDT'],  # Reduce size 30% for these
    'high_vol_reduction': 0.30,  # 30% reduction for high volatility
}

LOG_FILE = 'mean_reversion.log'
POSITIONS_FILE = 'mean_reversion_positions.json'

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
        log("[OK] Exchange connected successfully")
        return exchange
        
    except Exception as e:
        log(f"[ERR] Exchange init error: {e}")
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
    # Round to precision
    amount = round(amount, int(precision))
    # Ensure minimum amount
    amount = max(amount, float(min_amount))
    return amount

# ============ DATA FUNCTIONS ============
def fetch_ohlcv(exchange, symbol, timeframe='5m', limit=50):
    """Fetch candle data"""
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        log(f"[ERR] Fetch error for {symbol}: {e}")
        return None

def calculate_indicators(df):
    """Calculate mean reversion indicators"""
    # RSI
    df['rsi'] = talib.RSI(df['close'], timeperiod=CONFIG['rsi_period'])
    
    # Bollinger Bands
    df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(
        df['close'], 
        timeperiod=CONFIG['bb_period'], 
        nbdevup=CONFIG['bb_std'], 
        nbdevdn=CONFIG['bb_std']
    )
    df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    
    # ATR for volatility
    df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
    df['atr_pct'] = df['atr'] / df['close'] * 100
    
    # Volume
    df['volume_sma'] = df['volume'].rolling(window=20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma']
    
    return df

# ============ POSITION SIZING ============

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

# ============ SIGNAL GENERATION ============
def generate_signal(df, symbol):
    """Generate mean reversion signal"""
    if len(df) < 30:
        return None
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Skip if not enough data
    if pd.isna(current['rsi']) or pd.isna(current['bb_position']):
        return None
    
    signal = None
    
    # LONG Signal: Oversold bounce
    if (current['rsi'] < CONFIG['rsi_oversold'] and 
        current['bb_position'] < CONFIG['bb_threshold'] and
        current['volume_ratio'] > 0.8):
        
        confidence = min(95, 70 + (CONFIG['rsi_oversold'] - current['rsi']) * 1.5)
        
        if current['volume_ratio'] > 1.5:
            confidence += 5
        
        signal = {
            'symbol': symbol,
            'side': 'LONG',
            'confidence': confidence,
            'entry_price': current['close'],
            'rsi': current['rsi'],
            'bb_pos': current['bb_position'],
            'reason': f"RSI oversold ({current['rsi']:.1f}) + BB lower"
        }
    
    # SHORT Signal: Overbought reversal
    elif (current['rsi'] > CONFIG['rsi_overbought'] and 
          current['bb_position'] > (1 - CONFIG['bb_threshold']) and
          current['volume_ratio'] > 0.8):
        
        confidence = min(95, 70 + (current['rsi'] - CONFIG['rsi_overbought']) * 1.5)
        
        if current['volume_ratio'] > 1.5:
            confidence += 5
        
        signal = {
            'symbol': symbol,
            'side': 'SHORT',
            'confidence': confidence,
            'entry_price': current['close'],
            'rsi': current['rsi'],
            'bb_pos': current['bb_position'],
            'reason': f"RSI overbought ({current['rsi']:.1f}) + BB upper"
        }
    
    if signal and signal['confidence'] >= CONFIG['min_confidence']:
        # Calculate SL and TP
        if signal['side'] == 'LONG':
            signal['stop_loss'] = current['close'] * (1 - CONFIG['stop_loss_pct'])
            signal['take_profit'] = current['close'] * (1 + CONFIG['take_profit_pct'])
        else:
            signal['stop_loss'] = current['close'] * (1 + CONFIG['stop_loss_pct'])
            signal['take_profit'] = current['close'] * (1 - CONFIG['take_profit_pct'])
        
        # Round prices
        signal['stop_loss'] = round(signal['stop_loss'], 2)
        signal['take_profit'] = round(signal['take_profit'], 2)
        signal['entry_price'] = round(signal['entry_price'], 4)
        
        return signal
    
    return None

# ============ POSITION MANAGEMENT ============
def load_positions():
    """Load active positions"""
    try:
        if os.path.exists(POSITIONS_FILE):
            with open(POSITIONS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        log(f"[WARN] Error loading positions: {e}")
    return {}

def save_positions(positions):
    """Save positions to file"""
    try:
        with open(POSITIONS_FILE, 'w') as f:
            json.dump(positions, f, indent=2, default=str)
    except Exception as e:
        log(f"[WARN] Error saving positions: {e}")

def get_position_count():
    """Get number of active positions"""
    positions = load_positions()
    return len(positions)

# ============ TRADING FUNCTIONS ============
def open_position(exchange, signal):
    """Open a new position with proper TP/SL protection"""
    try:
        symbol = signal['symbol']
        side = signal['side']
        
        # Check if already have position in this symbol
        positions = load_positions()
        if symbol in positions:
            log(f"[SKIP] Already have position in {symbol}, skipping")
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
        log(f"[INFO] {symbol} precision: {amount_precision}, min: {min_amount}")
        
        # Set leverage
        try:
            exchange.set_leverage(CONFIG['leverage'], symbol)
        except Exception as e:
            log(f"[WARN] Leverage set error (may already be set): {e}")
        
        # Calculate position size with validated value
        raw_amount = position_value / signal['entry_price']
        amount = adjust_amount(raw_amount, amount_precision, min_amount)
        
        log(f"[INFO] Calculated amount: {raw_amount:.6f} -> Adjusted: {amount}")
        
        # Open market order
        order_side = 'buy' if side == 'LONG' else 'sell'
        
        order = exchange.create_order(
            symbol=symbol,
            type='market',
            side=order_side,
            amount=amount,
            params={'leverage': CONFIG['leverage']}
        )
        
        log(f"[OK] Market order filled: {order['id']}")
        
        # Set stop loss and take profit
        sl_price = signal['stop_loss']
        tp_price = signal['take_profit']
        sl_side = 'sell' if side == 'LONG' else 'buy'
        
        # triggerDirection: 1 = trigger when price rises to stopPrice
        # triggerDirection: 2 = trigger when price falls to stopPrice
        trigger_direction = 2 if side == 'LONG' else 1
        
        # FIXED: Use 'stop_market' instead of 'stop' for Bybit compatibility
        sl_params = {
            'stopPrice': sl_price,
            'reduceOnly': True,
            'triggerPrice': sl_price,
            'triggerDirection': 'falling' if side == 'LONG' else 'rising'
        }
        
        sl_order = exchange.create_order(
            symbol=symbol,
            type='stop_market',
            side=sl_side,
            amount=amount,
            params=sl_params
        )
        
        log(f"[OK] Stop Loss set @ ${sl_price:.4f}")
        
        # Create TP order
        tp_order = exchange.create_order(
            symbol=symbol,
            type='limit',
            side=sl_side,
            amount=amount,
            price=tp_price,
            params={'reduceOnly': True}
        )
        
        log(f"[OK] Take Profit set @ ${tp_price:.4f}")
        
        # Record position
        positions[symbol] = {
            'side': side,
            'entry_price': signal['entry_price'],
            'amount': amount,
            'stop_loss': sl_price,
            'take_profit': tp_price,
            'confidence': signal['confidence'],
            'entry_time': datetime.now().isoformat(),
            'order_id': order['id'],
            'sl_order_id': sl_order['id'],
            'tp_order_id': tp_order['id']
        }
        save_positions(positions)
        
        log(f"[OK] OPENED {side} {symbol} @ ${signal['entry_price']:.4f}")
        log(f"   SL: ${sl_price:.4f} | TP: ${tp_price:.4f} | Conf: {signal['confidence']:.0f}%")
        
        return True
        
    except Exception as e:
        log(f"[ERR] Error opening position: {e}")
        import traceback
        log(f"[ERR] Traceback: {traceback.format_exc()}")
        return False

def check_and_manage_positions(exchange):
    """Check existing positions and manage exits"""
    try:
        positions = load_positions()
        if not positions:
            return
        
        # Fetch current positions from exchange
        try:
            exchange_positions = exchange.fetch_positions()
            exchange_symbols = {p['symbol'] for p in exchange_positions if p['contracts'] and float(p['contracts']) != 0}
        except:
            exchange_symbols = set()
        
        # Clean up positions that no longer exist
        for symbol in list(positions.keys()):
            if symbol not in exchange_symbols:
                log(f"[CLEAN] Position {symbol} closed externally, removing from tracking")
                del positions[symbol]
        
        save_positions(positions)
        
    except Exception as e:
        log(f"[WARN] Error managing positions: {e}")

# ============ MAIN LOOP ============
def scan_markets():
    """Scan all markets for signals"""
    exchange = get_exchange()
    if not exchange:
        return
    
    log("[SCAN] Scanning for Mean Reversion signals...")
    
    signals = []
    
    for symbol in CONFIG['symbols']:
        try:
            df = fetch_ohlcv(exchange, symbol, CONFIG['timeframe'], CONFIG['lookback'])
            if df is None or len(df) < 30:
                continue
            
            df = calculate_indicators(df)
            signal = generate_signal(df, symbol)
            
            if signal:
                signals.append(signal)
                log(f"[SIG] {symbol}: {signal['side']} signal - {signal['confidence']:.0f}% conf")
                
        except Exception as e:
            log(f"[WARN] Error scanning {symbol}: {e}")
    
    return signals

def main_loop():
    """Main trading loop"""
    log("=" * 70)
    log("[START] Mean Reversion Bot Started")
    log(f"Config: {CONFIG['timeframe']} timeframe, {CONFIG['leverage']}x lev, {CONFIG['min_confidence']}% min conf")
    log("=" * 70)
    
    while True:
        try:
            # Check and manage existing positions
            exchange = get_exchange()
            if exchange:
                check_and_manage_positions(exchange)
            
            # Get current position count
            pos_count = get_position_count()
            
            # Scan for signals if under max positions
            if pos_count < CONFIG['max_positions']:
                signals = scan_markets()
                
                # Sort by confidence
                if signals:
                    signals.sort(key=lambda x: x['confidence'], reverse=True)
                    
                    # Take best signal
                    for signal in signals:
                        if signal['confidence'] >= CONFIG['min_confidence']:
                            if get_position_count() < CONFIG['max_positions']:
                                open_position(exchange, signal)
                            else:
                                break
            else:
                log(f"[WAIT] Max positions ({CONFIG['max_positions']}) reached, skipping scan")
            
            # Wait before next scan
            log(f"[SLEEP] Sleeping 60s... (Positions: {get_position_count()}/{CONFIG['max_positions']})")
            time.sleep(60)
            
        except Exception as e:
            log(f"[ERR] Main loop error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        log("[STOP] Bot stopped by user")
    except Exception as e:
        log(f"[FATAL] Fatal error: {e}")
