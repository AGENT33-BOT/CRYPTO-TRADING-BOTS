"""
Agent Bybit2 - SOL/USDT Specialist
Mean Reversion Strategy for $100 Account
"""

import ccxt
import pandas as pd
import numpy as np
import talib
import time
import json
from datetime import datetime
import os

# ============ CONFIGURATION ============
CONFIG = {
    'symbol': 'SOL/USDT:USDT',
    'timeframe': '1h',
    'lookback': 50,
    'leverage': 3,
    'position_size': 50,         # $50 per trade (50% of $100)
    'max_positions': 2,          # Max 2 positions
    'min_confidence': 75,
    
    'rsi_period': 14,
    'rsi_oversold': 35,
    'rsi_overbought': 65,
    'bb_period': 20,
    'bb_std': 2,
    'bb_threshold': 0.1,
    
    'stop_loss_pct': 0.015,      # 1.5% SL
    'take_profit_pct': 0.025,    # 2.5% TP
    'trailing_stop': True,
    'trailing_pct': 0.015,
}

LOG_FILE = 'crypto_trader/agent_bybit2/agent_bybit2.log'
POSITIONS_FILE = 'crypto_trader/agent_bybit2/agent_bybit2_positions.json'
API_KEY = 'aLz3ySrF9kMZubmqDR'
API_SECRET = '8SlpKyX7vleDu1loJiFePGWfnynJRXZXaD2z'

os.makedirs('crypto_trader/agent_bybit2', exist_ok=True)

# ============ LOGGER ============
def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {msg}"
    try:
        print(log_msg)
    except:
        print(log_msg.encode('ascii', 'replace').decode())
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_msg + '\n')

# ============ EXCHANGE ============
def get_exchange():
    exchange = ccxt.bybit({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })
    exchange.set_sandbox_mode(False)
    return exchange

# ============ DATA & INDICATORS ============
def fetch_data(exchange, symbol, timeframe, limit):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def calculate_indicators(df):
    df['rsi'] = talib.RSI(df['close'], timeperiod=CONFIG['rsi_period'])
    df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(
        df['close'], timeperiod=CONFIG['bb_period'], nbdevup=CONFIG['bb_std'], nbdevdn=CONFIG['bb_std']
    )
    df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    df['volume_sma'] = df['volume'].rolling(window=20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma']
    return df

# ============ POSITIONS ============
def load_positions():
    if os.path.exists(POSITIONS_FILE):
        with open(POSITIONS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_positions(positions):
    with open(POSITIONS_FILE, 'w') as f:
        json.dump(positions, f, indent=2, default=str)

# ============ TRADING FUNCTIONS ============
def adjust_amount(amount, symbol_info):
    min_amount = symbol_info['limits']['amount']['min'] or 0.001
    precision = len(str(symbol_info['limits']['amount']['min'] or 0.001).split('.')[-1]) if '.' in str(symbol_info['limits']['amount']['min'] or 0.001) else 3
    adjusted = max(min_amount, round(amount, precision))
    return adjusted

def get_signal(df):
    if len(df) < 20:
        return None
    
    current = df.iloc[-1]
    
    # Long: RSI oversold + BB lower touch
    if (current['rsi'] < CONFIG['rsi_oversold'] and 
        current['bb_position'] < CONFIG['bb_threshold'] and
        current['volume_ratio'] > 1.0):
        return {
            'signal': 'LONG',
            'confidence': min(95, 75 + (CONFIG['rsi_oversold'] - current['rsi']) * 1.5),
            'entry': current['close'],
            'sl': current['close'] * (1 - CONFIG['stop_loss_pct']),
            'tp': current['close'] * (1 + CONFIG['take_profit_pct'])
        }
    
    # Short: RSI overbought + BB upper touch
    if (current['rsi'] > CONFIG['rsi_overbought'] and 
        current['bb_position'] > (1 - CONFIG['bb_threshold']) and
        current['volume_ratio'] > 1.0):
        return {
            'signal': 'SHORT',
            'confidence': min(95, 75 + (current['rsi'] - CONFIG['rsi_overbought']) * 1.5),
            'entry': current['close'],
            'sl': current['close'] * (1 + CONFIG['stop_loss_pct']),
            'tp': current['close'] * (1 - CONFIG['take_profit_pct'])
        }
    
    return None

def open_position(exchange, symbol, signal):
    positions = load_positions()
    if len(positions) >= CONFIG['max_positions']:
        return False
    
    side = 'Buy' if signal['signal'] == 'LONG' else 'Sell'
    
    try:
        # Set leverage
        exchange.set_leverage(CONFIG['leverage'], symbol)
        
        # Get market info
        markets = exchange.load_markets()
        symbol_info = markets[symbol]
        
        # Calculate position size
        price = signal['entry']
        amount_usd = CONFIG['position_size']
        amount = amount_usd / price
        amount = adjust_amount(amount, symbol_info)
        
        # Place market order
        order = exchange.create_market_buy_order(symbol, amount) if side == 'Buy' else exchange.create_market_sell_order(symbol, amount)
        
        entry_price = order['average'] or order['price'] or price
        
        # Set TP/SL
        tp_price = signal['tp']
        sl_price = signal['sl']
        
        trigger_direction = 2 if signal['signal'] == 'LONG' else 1
        
        exchange.create_order(
            symbol=symbol,
            type='limit',
            side='Sell' if side == 'Buy' else 'Buy',
            amount=amount,
            price=tp_price,
            params={
                'reduceOnly': True,
                'takeProfit': str(tp_price),
                'triggerDirection': trigger_direction
            }
        )
        
        exchange.create_order(
            symbol=symbol,
            type='limit',
            side='Sell' if side == 'Buy' else 'Buy',
            amount=amount,
            price=sl_price,
            params={
                'reduceOnly': True,
                'stopLoss': str(sl_price),
                'triggerDirection': trigger_direction
            }
        )
        
        pos_id = f"{symbol}_{int(time.time())}"
        positions[pos_id] = {
            'symbol': symbol,
            'side': signal['signal'],
            'entry': entry_price,
            'amount': amount,
            'tp': tp_price,
            'sl': sl_price,
            'time': datetime.now().isoformat()
        }
        save_positions(positions)
        
        log(f"✅ OPENED {signal['signal']} on {symbol} @ {entry_price:.4f} | Amount: {amount:.4f} | TP: {tp_price:.4f} | SL: {sl_price:.4f}")
        return True
        
    except Exception as e:
        log(f"❌ Error opening position: {e}")
        return False

def check_positions(exchange):
    try:
        positions = exchange.fetch_positions([CONFIG['symbol']])
        open_pos = [p for p in positions if float(p.get('contracts', 0)) != 0]
        
        saved = load_positions()
        
        # Clean up closed positions
        closed = []
        for pos_id, pos in list(saved.items()):
            still_open = any(p['symbol'] == pos['symbol'] for p in open_pos)
            if not still_open:
                closed.append(pos_id)
        
        for pos_id in closed:
            log(f"📤 Position closed: {saved[pos_id]['symbol']}")
            del saved[pos_id]
        
        if closed:
            save_positions(saved)
        
        return len(open_pos)
        
    except Exception as e:
        log(f"❌ Error checking positions: {e}")
        return 0

# ============ MAIN LOOP ============
def run_cycle():
    log("="*60)
    log("Agent Bybit2 - SOL/USDT Mean Reversion Bot")
    log("="*60)
    
    try:
        exchange = get_exchange()
        
        # Test connection
        balance = exchange.fetch_balance()
        usdt = balance.get('USDT', {}).get('free', 0)
        log(f"💰 Balance: {usdt:.2f} USDT available")
        
        # Check existing positions
        open_count = check_positions(exchange)
        log(f"📊 Open positions: {open_count}/{CONFIG['max_positions']}")
        
        if open_count >= CONFIG['max_positions']:
            log("Max positions reached, skipping signal check")
            return
        
        # Fetch data and check for signals
        log(f"📈 Fetching {CONFIG['timeframe']} data for {CONFIG['symbol']}...")
        df = fetch_data(exchange, CONFIG['symbol'], CONFIG['timeframe'], CONFIG['lookback'])
        df = calculate_indicators(df)
        
        signal = get_signal(df)
        
        if signal and signal['confidence'] >= CONFIG['min_confidence']:
            log(f"🎯 SIGNAL: {signal['signal']} @ {signal['entry']:.4f} (confidence: {signal['confidence']:.1f}%)")
            open_position(exchange, CONFIG['symbol'], signal)
        else:
            rsi = df.iloc[-1]['rsi']
            bb_pos = df.iloc[-1]['bb_position']
            log(f"⏳ No signal. RSI: {rsi:.1f}, BB Pos: {bb_pos:.2f}")
        
        log("Cycle complete")
        
    except Exception as e:
        log(f"❌ Error in main cycle: {e}")

if __name__ == "__main__":
    log("\n" + "="*60)
    log("AGENT BYBIT2 STARTING")
    log("Account: $100 SOL/USDT Specialist")
    log("="*60)
    
    while True:
        try:
            run_cycle()
            log("Sleeping 60 seconds...\n")
            time.sleep(60)
        except KeyboardInterrupt:
            log("Shutting down...")
            break
        except Exception as e:
            log(f"Error: {e}")
            time.sleep(60)
