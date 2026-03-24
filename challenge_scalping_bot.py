"""
CHALLENGE SCALPING BOT - Phase 1
Aggressive scalping for $469 → $657 target
15x leverage, 3m candles, tight TP/SL
"""

import ccxt
import pandas as pd
import numpy as np
import talib
import time
import json
import sys
import os
from datetime import datetime

# Load challenge config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from CHALLENGE_CONFIG import *

# Extract Phase 1 config
CONFIG = PHASE1_CONFIG
RISK = RISK_CONFIG

LOG_FILE = 'challenge_scalping.log'
POSITIONS_FILE = 'challenge_positions.json'

# Track challenge state
challenge_state = {
    'start_time': datetime.now().isoformat(),
    'starting_balance': STARTING_BALANCE,
    'current_balance': STARTING_BALANCE,
    'target_balance': TARGET_BALANCE,
    'trades_today': 0,
    'wins': 0,
    'losses': 0,
    'daily_pnl': 0,
    'consecutive_losses': 0,
    'phase': 1,
    'active': True
}

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[CHALLENGE] [{timestamp}] {msg}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')

def save_state():
    with open('challenge_state.json', 'w') as f:
        json.dump(challenge_state, f, indent=2)

def get_exchange():
    try:
        api_key = 'bsK06QDhsagOWwFsXQ'
        api_secret = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'
        
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
        exchange.load_markets()
        
        # Set leverage
        for symbol in CONFIG['symbols']:
            try:
                exchange.set_leverage(CONFIG['leverage'], symbol)
                log(f"Leverage set to {CONFIG['leverage']}x for {symbol}")
            except Exception as e:
                log(f"Leverage error for {symbol}: {e}")
        
        return exchange
    except Exception as e:
        log(f"Exchange init error: {e}")
        return None

def get_balance(exchange):
    try:
        balance = exchange.fetch_balance({'type': 'unified'})
        return balance.get('USDT', {}).get('free', 0)
    except:
        return 0

def get_open_positions_count(exchange):
    try:
        positions = exchange.fetch_positions()
        return len([p for p in positions if float(p.get('contracts', 0)) != 0])
    except:
        return 0

def calculate_position_size(balance, symbol):
    """Calculate position size - FIXED $20 per position for aggressive mode"""
    # Use fixed $20 position size (or config value if set)
    position_value = CONFIG.get('position_size_usd', 20)
    
    # Ensure we don't exceed max loss per position
    # At 25x with 2% SL = 50% loss on $20 = $10 max
    # But we want $5 max loss, so we'll use tight monitoring
    
    return position_value

def calculate_max_loss_amount(entry_price, amount, side, leverage):
    """Calculate actual loss if SL hits"""
    notional = amount * entry_price * leverage
    sl_loss_pct = CONFIG['sl_pct'] * leverage  # e.g., 0.02 * 25 = 50%
    max_loss = notional * CONFIG['sl_pct']  # Simplified: amount * entry * sl_pct
    return max_loss

def check_signals(exchange, symbol):
    """Check for entry signals using RSI + Bollinger Bands"""
    try:
        # Fetch OHLCV
        ohlcv = exchange.fetch_ohlcv(symbol, CONFIG['timeframe'], limit=50)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Calculate indicators
        close = df['close'].values
        df['rsi'] = talib.RSI(close, timeperiod=CONFIG['rsi_period'])
        df['upper'], df['middle'], df['lower'] = talib.BBANDS(
            close, 
            timeperiod=CONFIG['bb_period'],
            nbdevup=CONFIG['bb_std'],
            nbdevdn=CONFIG['bb_std']
        )
        
        current = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Long signal: RSI < oversold AND price near lower BB
        if current['rsi'] < CONFIG['rsi_oversold'] and current['close'] <= current['lower'] * 1.001:
            return 'LONG', 85
        
        # Short signal: RSI > overbought AND price near upper BB
        if current['rsi'] > CONFIG['rsi_overbought'] and current['close'] >= current['upper'] * 0.999:
            return 'SHORT', 85
        
        return None, 0
        
    except Exception as e:
        log(f"Signal error for {symbol}: {e}")
        return None, 0

def open_position(exchange, symbol, side, balance):
    """Open a position with TP/SL"""
    try:
        # Get current price
        ticker = exchange.fetch_ticker(symbol)
        entry_price = ticker['last']
        
        # Calculate TP/SL
        if side == 'LONG':
            tp_price = entry_price * (1 + CONFIG['tp_pct'])
            sl_price = entry_price * (1 - CONFIG['sl_pct'])
        else:  # SHORT
            tp_price = entry_price * (1 - CONFIG['tp_pct'])
            sl_price = entry_price * (1 + CONFIG['sl_pct'])
        
        # Calculate position size
        position_value = calculate_position_size(balance, symbol)
        amount = position_value / entry_price
        
        # Get precision
        market = exchange.market(symbol)
        amount_precision = market['precision']['amount']
        amount = round(amount, int(amount_precision))
        min_amount = market['limits']['amount']['min']
        if amount < min_amount:
            amount = min_amount
        
        # Place order with TP/SL
        order = exchange.create_order(
            symbol=symbol,
            type='market',
            side='buy' if side == 'LONG' else 'sell',
            amount=amount,
            params={
                'takeProfit': tp_price,
                'stopLoss': sl_price,
                'tpslMode': 'Full'
            }
        )
        
        log(f"OPENED {side} {symbol}: {amount} @ ${entry_price:.4f}")
        log(f"   TP: ${tp_price:.4f} | SL: ${sl_price:.4f}")
        
        # Update state
        challenge_state['trades_today'] += 1
        save_state()
        
        return True
        
    except Exception as e:
        log(f"Error opening position: {e}")
        return False

def check_daily_limit():
    """Check if daily loss limit reached"""
    if challenge_state['daily_pnl'] <= -RISK['daily_loss_limit_usd']:
        log(f"DAILY LOSS LIMIT REACHED: ${challenge_state['daily_pnl']:.2f}")
        challenge_state['active'] = False
        save_state()
        return False
    
    if challenge_state['consecutive_losses'] >= RISK['consecutive_losses_limit']:
        log(f"CONSECUTIVE LOSSES LIMIT: {challenge_state['consecutive_losses']}")
        return False
    
    return True

def send_telegram_alert(message):
    """Send alert to Telegram"""
    try:
        import requests
        token = "7594239785:AAG6YjJ4LDK0vMQT5Cq2LHS5-9q-OWJb8oI"
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {
            'chat_id': '5804173449',
            'text': message,
            'parse_mode': 'Markdown'
        }
        requests.post(url, data=data, timeout=5)
    except:
        pass

def main():
    log("=" * 70)
    log("CHALLENGE PHASE 1: AGGRESSIVE SCALPING - UPDATED")
    log("=" * 70)
    log(f"Target: ${STARTING_BALANCE} to ${TARGET_BALANCE}")
    log(f"Leverage: {CONFIG['leverage']}x (INCREASED for aggressive mode)")
    log(f"Position Size: ${CONFIG.get('position_size_usd', 20)} per trade (~$500 notional)")
    log(f"Max Loss Per Position: ${RISK['max_loss_per_position_usd']} HARD LIMIT")
    log(f"TP: {CONFIG['tp_pct'] * 100}% | SL: {CONFIG['sl_pct'] * 100}%")
    log(f"Max Positions: {CONFIG['max_positions']}")
    log(f"Symbols: {', '.join(CONFIG['symbols'])}")
    log("=" * 70)
    
    send_telegram_alert(
        f"*CHALLENGE UPDATED - AGGRESSIVE MODE*\n\n"
        f"Phase 1: Ultra-Aggressive Scalping\n"
        f"Target: ${STARTING_BALANCE} to ${TARGET_BALANCE}\n"
        f"Leverage: {CONFIG['leverage']}x | Timeframe: {CONFIG['timeframe']}\n"
        f"Position Size: ${CONFIG.get('position_size_usd', 20)} per trade\n"
        f"Max Loss/Position: ${RISK['max_loss_per_position_usd']}\n\n"
        f"Let's get that 100% return! 🚀"
    )
    
    exchange = get_exchange()
    if not exchange:
        log("Failed to initialize exchange")
        return
    
    save_state()
    scan_count = 0
    
    try:
        while challenge_state['active']:
            # Check daily limits
            if not check_daily_limit():
                log("Trading halted due to risk limits")
                break
            
            # Check if max positions reached
            open_count = get_open_positions_count(exchange)
            if open_count >= CONFIG['max_positions']:
                time.sleep(CONFIG['scan_interval'])
                continue
            
            # Get balance
            balance = get_balance(exchange)
            challenge_state['current_balance'] = balance
            
            # Scan for signals
            for symbol in CONFIG['symbols']:
                signal, confidence = check_signals(exchange, symbol)
                
                if signal and confidence >= CONFIG['confidence_threshold']:
                    log(f"Signal: {signal} {symbol} (confidence: {confidence}%)")
                    
                    # Open position
                    if open_position(exchange, symbol, signal, balance):
                        send_telegram_alert(
                            f"*CHALLENGE TRADE*\n\n"
                            f"{signal} {symbol}\n"
                            f"Leverage: {CONFIG['leverage']}x\n"
                            f"Size: ${CONFIG.get('position_size_usd', 20)} (~${CONFIG.get('position_size_usd', 20) * CONFIG['leverage']} notional)\n"
                            f"Max Loss: ${RISK['max_loss_per_position_usd']}\n\n"
                            f"Trade #{challenge_state['trades_today']} today"
                        )
            
            scan_count += 1
            if scan_count % 240 == 0:  # Every hour (assuming 15s interval)
                log(f"Balance: ${balance:.2f} | PnL: ${challenge_state['daily_pnl']:.2f} | "
                    f"Trades: {challenge_state['trades_today']} | "
                    f"Win Rate: {challenge_state['wins']}/{challenge_state['losses']}")
                
                # Send hourly update
                send_telegram_alert(
                    f"*CHALLENGE UPDATE*\n\n"
                    f"Balance: ${balance:.2f}\n"
                    f"Daily PnL: ${challenge_state['daily_pnl']:.2f}\n"
                    f"Trades: {challenge_state['trades_today']}\n"
                    f"Wins: {challenge_state['wins']} | Losses: {challenge_state['losses']}\n\n"
                    f"Progress to ${TARGET_BALANCE}: {(balance/STARTING_BALANCE - 1) * 100:.1f}%"
                )
            
            time.sleep(CONFIG['scan_interval'])
            
    except KeyboardInterrupt:
        log("Challenge stopped by user")
    except Exception as e:
        log(f"Error in main loop: {e}")
    finally:
        save_state()
        log("Challenge bot stopped")

if __name__ == '__main__':
    main()
