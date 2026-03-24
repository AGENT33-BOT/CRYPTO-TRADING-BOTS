"""
Crypto.com Trading Agent for Pablobots
Strategy: Scalping with RSI + Bollinger Bands on 1m/5m timeframes
"""

import ccxt
import pandas as pd
import numpy as np
import talib
import time
import json
import os
import sys
from datetime import datetime

# ============ CONFIGURATION ============
CONFIG = {
    'exchange_name': 'cryptocom',
    'symbols': [
        'BTC/USD:USD',    # Crypto.com uses USD pairs
        'ETH/USD:USD',
        'SOL/USD:USD',
        'XRP/USD:USD',
        'LINK/USD:USD',
        'AVAX/USD:USD',
        'DOGE/USD:USD',
        'MATIC/USD:USD',
    ],
    'timeframe': '1m',
    'lookback': 50,
    'leverage': 3,               # Conservative leverage for Crypto.com
    'position_size_pct': 0.05,   # 5% per trade
    'max_positions': 3,
    'min_confidence': 80,
    
    # Risk management
    'max_position_pct': 0.20,    # Max 20% of account per position
    'min_free_balance': 20,      # Minimum $20 free
    
    # Strategy params
    'rsi_period': 7,
    'rsi_oversold': 30,
    'rsi_overbought': 70,
    'bb_period': 20,
    'bb_std': 2,
    'profit_target': 0.008,      # 0.8%
    'stop_loss': 0.005,          # 0.5%
    'max_hold_minutes': 20,      # 20 min max hold
    
    # Exchange specific
    'testnet': False,            # Crypto.com doesn't have testnet for futures
    'rate_limit': True,
}

LOG_FILE = 'crypto_com_trading.log'
POSITIONS_FILE = 'crypto_com_positions.json'
API_CREDENTIALS_FILE = 'crypto_com_credentials.json'

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_msg + '\n')
    except:
        pass

def load_credentials():
    """Load API credentials from file or environment"""
    try:
        # First check file
        if os.path.exists(API_CREDENTIALS_FILE):
            with open(API_CREDENTIALS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        log(f"[WARN] Could not load credentials file: {e}")
    
    # Fallback to environment
    return {
        'api_key': os.environ.get('CRYPTOCOM_API_KEY', ''),
        'api_secret': os.environ.get('CRYPTOCOM_API_SECRET', ''),
    }

def save_credentials(creds):
    """Save API credentials to file"""
    try:
        with open(API_CREDENTIALS_FILE, 'w') as f:
            json.dump(creds, f, indent=2)
        log("[OK] Credentials saved")
    except Exception as e:
        log(f"[ERR] Could not save credentials: {e}")

def get_exchange():
    """Initialize Crypto.com exchange"""
    try:
        creds = load_credentials()
        api_key = creds.get('api_key', '')
        api_secret = creds.get('api_secret', '')
        
        if not api_key or not api_secret:
            log("[ERR] Crypto.com API credentials not configured")
            log("[INFO] Set CRYPTOCOM_API_KEY and CRYPTOCOM_API_SECRET environment variables")
            log("[INFO] Or create crypto_com_credentials.json file")
            return None
        
        exchange = ccxt.cryptocom({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': CONFIG['rate_limit'],
            'options': {
                'defaultType': 'swap',  # For perpetual futures
            }
        })
        
        # Load markets to test connection
        exchange.load_markets()
        log(f"[OK] Connected to Crypto.com")
        return exchange
        
    except Exception as e:
        log(f"[ERR] Exchange connection error: {e}")
        return None

def fetch_ohlcv(exchange, symbol, timeframe='1m', limit=50):
    """Fetch OHLCV data"""
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        log(f"[ERR] Fetch error for {symbol}: {e}")
        return None

def calculate_indicators(df):
    """Calculate technical indicators"""
    # RSI
    df['rsi'] = talib.RSI(df['close'], timeperiod=CONFIG['rsi_period'])
    
    # Bollinger Bands
    df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(
        df['close'], 
        timeperiod=CONFIG['bb_period'],
        nbdevup=CONFIG['bb_std'],
        nbdevdn=CONFIG['bb_std']
    )
    
    # EMA
    df['ema_9'] = talib.EMA(df['close'], timeperiod=9)
    df['ema_20'] = talib.EMA(df['close'], timeperiod=20)
    
    # ATR
    df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=7)
    
    return df

def generate_signal(df, symbol):
    """Generate trading signal based on RSI + BB strategy"""
    if len(df) < 25:
        return None
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    
    if pd.isna(current['rsi']) or pd.isna(current['bb_lower']):
        return None
    
    signal = None
    confidence = 0
    reason = ""
    
    # LONG Signal: RSI oversold + price near BB lower band
    if (current['rsi'] < CONFIG['rsi_oversold'] and
        current['close'] <= current['bb_lower'] * 1.002 and
        prev['rsi'] < current['rsi']):  # RSI turning up
        
        confidence = 70 + (CONFIG['rsi_oversold'] - current['rsi'])
        confidence = min(95, confidence)
        reason = f"RSI oversold ({current['rsi']:.1f}) + BB lower bounce"
        
        signal = {
            'symbol': symbol,
            'side': 'LONG',
            'confidence': confidence,
            'entry_price': current['close'],
            'entry_time': datetime.now(),
            'reason': reason
        }
    
    # SHORT Signal: RSI overbought + price near BB upper band
    elif (current['rsi'] > CONFIG['rsi_overbought'] and
          current['close'] >= current['bb_upper'] * 0.998 and
          prev['rsi'] > current['rsi']):  # RSI turning down
        
        confidence = 70 + (current['rsi'] - CONFIG['rsi_overbought'])
        confidence = min(95, confidence)
        reason = f"RSI overbought ({current['rsi']:.1f}) + BB upper rejection"
        
        signal = {
            'symbol': symbol,
            'side': 'SHORT',
            'confidence': confidence,
            'entry_price': current['close'],
            'entry_time': datetime.now(),
            'reason': reason
        }
    
    if signal and signal['confidence'] >= CONFIG['min_confidence']:
        # Calculate TP/SL
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
    """Load open positions from file"""
    try:
        if os.path.exists(POSITIONS_FILE):
            with open(POSITIONS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        log(f"[WARN] Could not load positions: {e}")
    return {}

def save_positions(positions):
    """Save positions to file"""
    try:
        with open(POSITIONS_FILE, 'w') as f:
            json.dump(positions, f, indent=2, default=str)
    except Exception as e:
        log(f"[ERR] Could not save positions: {e}")

def get_position_count():
    """Get current position count"""
    return len(load_positions())

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

def calculate_position_size(exchange, symbol, entry_price):
    """Calculate position size based on risk management"""
    try:
        balance = exchange.fetch_balance()
        usdt_balance = float(balance.get('USD', {}).get('free', 0))
        total_balance = float(balance.get('USD', {}).get('total', 0))
        
        if usdt_balance < CONFIG['min_free_balance']:
            log(f"[RISK] Insufficient free balance: ${usdt_balance:.2f}")
            return 0
        
        # Calculate position value
        position_value = total_balance * CONFIG['position_size_pct']
        
        # Apply max position limit
        max_position_value = total_balance * CONFIG['max_position_pct']
        position_value = min(position_value, max_position_value)
        
        # Calculate amount
        amount = position_value / entry_price
        
        return amount
        
    except Exception as e:
        log(f"[ERR] Position sizing error: {e}")
        return 0

def open_position(exchange, signal):
    """Open a new position with TP/SL"""
    try:
        symbol = signal['symbol']
        side = signal['side']
        
        # Check if already in position
        positions = load_positions()
        if symbol in positions:
            log(f"[SKIP] Already in position for {symbol}")
            return False
        
        # Calculate position size
        amount = calculate_position_size(exchange, symbol, signal['entry_price'])
        if amount <= 0:
            return False
        
        # Get precision
        amount_precision, min_amount = get_symbol_precision(exchange, symbol)
        amount = adjust_amount(amount, amount_precision, min_amount)
        
        # Set leverage
        try:
            exchange.set_leverage(CONFIG['leverage'], symbol)
        except:
            pass
        
        # Create market order
        order_side = 'buy' if side == 'LONG' else 'sell'
        
        log(f"[ORDER] Opening {side} {symbol} @ ${signal['entry_price']:.4f}, Size: {amount}")
        
        order = exchange.create_order(
            symbol=symbol,
            type='market',
            side=order_side,
            amount=amount,
            params={'leverage': CONFIG['leverage']}
        )
        
        # Create stop loss
        sl_side = 'sell' if side == 'LONG' else 'buy'
        
        try:
            sl_order = exchange.create_order(
                symbol=symbol,
                type='stop_market',
                side=sl_side,
                amount=amount,
                params={
                    'stopPrice': signal['stop_loss'],
                    'reduceOnly': True,
                }
            )
            sl_order_id = sl_order['id']
        except Exception as e:
            log(f"[WARN] SL order failed: {e}")
            sl_order_id = None
        
        # Create take profit
        try:
            tp_order = exchange.create_order(
                symbol=symbol,
                type='limit',
                side=sl_side,
                amount=amount,
                price=signal['take_profit'],
                params={'reduceOnly': True}
            )
            tp_order_id = tp_order['id']
        except Exception as e:
            log(f"[WARN] TP order failed: {e}")
            tp_order_id = None
        
        # Save position
        positions[symbol] = {
            'side': side,
            'entry_price': signal['entry_price'],
            'amount': amount,
            'stop_loss': signal['stop_loss'],
            'take_profit': signal['take_profit'],
            'entry_time': signal['entry_time'].isoformat(),
            'order_id': order['id'],
            'sl_order_id': sl_order_id,
            'tp_order_id': tp_order_id,
        }
        save_positions(positions)
        
        log(f"[OK] Position opened: {side} {symbol}")
        log(f"   SL: ${signal['stop_loss']:.4f} | TP: ${signal['take_profit']:.4f}")
        
        return True
        
    except Exception as e:
        log(f"[ERR] Open position error: {e}")
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
                    log(f"[TIME] Time exit for {symbol} ({hold_time:.0f} min)")
                    del positions[symbol]
                except Exception as e:
                    log(f"[WARN] Time exit error: {e}")
        
        save_positions(positions)
    except Exception as e:
        log(f"[WARN] Exit check error: {e}")

def check_api_setup():
    """Check if API is properly configured"""
    creds = load_credentials()
    if not creds.get('api_key') or not creds.get('api_secret'):
        log("="*60)
        log("CRYPTO.COM API SETUP REQUIRED")
        log("="*60)
        log("")
        log("Please set your Crypto.com API credentials:")
        log("")
        log("Option 1: Environment Variables")
        log("  set CRYPTOCOM_API_KEY=your_api_key")
        log("  set CRYPTOCOM_API_SECRET=your_api_secret")
        log("")
        log("Option 2: Create crypto_com_credentials.json:")
        log('  {"api_key": "your_key", "api_secret": "your_secret"}')
        log("")
        log("Get API keys from: https://crypto.com/exchange/settings/api")
        log("="*60)
        return False
    return True

def main_loop():
    """Main trading loop"""
    log("="*70)
    log("🚀 CRYPTO.COM TRADING AGENT STARTED")
    log(f"Strategy: RSI + Bollinger Bands | Timeframe: {CONFIG['timeframe']}")
    log(f"Max Positions: {CONFIG['max_positions']} | Leverage: {CONFIG['leverage']}x")
    log("="*70)
    
    # Check API setup
    if not check_api_setup():
        log("[ERR] API not configured. Exiting.")
        return
    
    while True:
        try:
            exchange = get_exchange()
            if not exchange:
                log("[ERR] Could not connect to exchange. Retrying in 60s...")
                time.sleep(60)
                continue
            
            # Check time-based exits
            check_time_based_exits(exchange)
            
            # Scan for opportunities
            if get_position_count() < CONFIG['max_positions']:
                log("[SCAN] Scanning for opportunities...")
                
                for symbol in CONFIG['symbols']:
                    try:
                        # Check if symbol exists
                        if symbol not in exchange.markets:
                            continue
                        
                        df = fetch_ohlcv(exchange, symbol, CONFIG['timeframe'], CONFIG['lookback'])
                        if df is None:
                            continue
                        
                        df = calculate_indicators(df)
                        signal = generate_signal(df, symbol)
                        
                        if signal and signal['confidence'] >= CONFIG['min_confidence']:
                            log(f"[SIG] {symbol}: {signal['side']} ({signal['confidence']:.0f}%) - {signal['reason']}")
                            
                            if get_position_count() < CONFIG['max_positions']:
                                open_position(exchange, signal)
                    
                    except Exception as e:
                        continue
            else:
                log(f"[WAIT] Max positions reached ({get_position_count()}/{CONFIG['max_positions']})")
            
            log(f"[SLEEP] Sleep 30s... Positions: {get_position_count()}")
            time.sleep(30)
            
        except KeyboardInterrupt:
            log("[STOP] Interrupted by user")
            break
        except Exception as e:
            log(f"[ERR] Loop error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        log("[STOP] Trading agent stopped")
