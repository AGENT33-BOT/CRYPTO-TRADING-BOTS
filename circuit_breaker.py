#!/usr/bin/env python3
"""
CIRCUIT BREAKER - Automatic Risk Management System
Stops trading when losses exceed limits
"""
import ccxt
import time
import os
import sys
from datetime import datetime
import json

# RISK LIMITS (ADJUST THESE)
MAX_DAILY_LOSS_USD = 10.0          # Stop all trading if day loss exceeds this
MAX_POSITION_LOSS_USD = 5.0        # Close position if loss exceeds this
MIN_FREE_BALANCE_USD = 50.0        # Minimum free balance required
MAX_POSITION_SIZE_PCT = 15.0       # Max position size as % of account

# LOG FILES
LOG_FILE = 'circuit_breaker.log'
STATE_FILE = 'circuit_breaker_state.json'

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')

def send_alert(message):
    """Send Telegram alert"""
    try:
        import requests
        token = '7594239785:AAG6YjJ4LDK0vMQT5Cq2LHS5-9q-OWJb8oI'
        chat_id = '5804173449'
        requests.post(
            f'https://api.telegram.org/bot{token}/sendMessage',
            json={'chat_id': chat_id, 'text': f"🚨 CIRCUIT BREAKER\n\n{message}"},
            timeout=5
        )
    except:
        pass

def get_exchange():
    """Initialize exchange"""
    return ccxt.bybit({
        'apiKey': 'bsK06QDhsagOWwFsXQ',
        'secret': 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa',
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })

def load_state():
    """Load circuit breaker state"""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {'daily_start_pnl': None, 'stopped': False, 'stop_time': None}

def save_state(state):
    """Save circuit breaker state"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def stop_all_bots():
    """Stop all trading bots"""
    log("[ACTION] Stopping all bots...")
    
    # List of bot processes to stop
    bot_scripts = [
        'mean_reversion_trader.py',
        'momentum_trader.py',
        'scalping_bot.py',
        'grid_trading_bot.py',
        'funding_arbitrage.py'
    ]
    
    stopped = []
    for script in bot_scripts:
        try:
            os.system(f'taskkill /F /IM python.exe /FI "WINDOWTITLE eq {script}" 2>nul')
            stopped.append(script)
            log(f"  [STOPPED] {script}")
        except:
            log(f"  [FAILED] {script}")
    
    return stopped

def close_position(exchange, symbol, position):
    """Close a specific position"""
    try:
        side = position['side']
        size = abs(float(position['contracts']))
        
        if side == 'long':
            order = exchange.create_market_sell_order(symbol, size)
        else:
            order = exchange.create_market_buy_order(symbol, size)
        
        log(f"[CLOSED] {symbol} {side} {size}")
        return True
    except Exception as e:
        log(f"[ERROR] Could not close {symbol}: {e}")
        return False

def check_and_break():
    """Main circuit breaker check"""
    log("=" * 60)
    log("CIRCUIT BREAKER CHECK")
    log("=" * 60)
    
    try:
        exchange = get_exchange()
        balance = exchange.fetch_balance()
        positions = exchange.fetch_positions()
        
        total_balance = float(balance.get('USDT', {}).get('total', 0))
        free_balance = float(balance.get('USDT', {}).get('free', 0))
        
        # Get unrealized P&L
        total_pnl = 0
        active_positions = []
        
        for pos in positions:
            contracts = float(pos.get('contracts', 0))
            if contracts != 0:
                pnl = float(pos.get('unrealizedPnl', 0))
                total_pnl += pnl
                active_positions.append({
                    'symbol': pos['symbol'],
                    'side': pos['side'],
                    'size': contracts,
                    'pnl': pnl,
                    'entry': float(pos.get('entryPrice', 0))
                })
        
        log(f"Total Balance: ${total_balance:.2f}")
        log(f"Free Balance: ${free_balance:.2f}")
        log(f"Unrealized P&L: ${total_pnl:.2f}")
        log(f"Active Positions: {len(active_positions)}")
        
        # Load state
        state = load_state()
        
        # Check if already stopped
        if state.get('stopped'):
            # Check if we should resume (after 1 hour cooldown)
            stop_time = state.get('stop_time')
            if stop_time:
                elapsed = (datetime.now() - datetime.fromisoformat(stop_time)).total_seconds()
                if elapsed > 3600:  # 1 hour
                    log("[RESUME] Circuit breaker cooldown expired. Resuming...")
                    state['stopped'] = False
                    state['stop_time'] = None
                    state['daily_start_pnl'] = total_pnl
                    save_state(state)
                    send_alert("Circuit breaker reset. Trading resuming.")
                else:
                    log(f"[BLOCKED] Trading stopped. Cooldown: {int(3600-elapsed)}s remaining")
                    return False
            else:
                log("[BLOCKED] Trading stopped. Manual reset required.")
                return False
        
        # Initialize daily P&L if not set
        if state.get('daily_start_pnl') is None:
            state['daily_start_pnl'] = total_pnl
            save_state(state)
            log(f"[INIT] Daily P&L baseline: ${total_pnl:.2f}")
        
        daily_pnl = total_pnl - state['daily_start_pnl']
        log(f"Daily P&L: ${daily_pnl:.2f}")
        
        # CHECK 1: Daily loss limit
        if daily_pnl < -MAX_DAILY_LOSS_USD:
            log(f"🚨 DAILY LOSS LIMIT EXCEEDED: ${daily_pnl:.2f} < -${MAX_DAILY_LOSS_USD}")
            send_alert(f"CIRCUIT BREAKER TRIGGERED\n\nDaily Loss: ${daily_pnl:.2f}\nLimit: -${MAX_DAILY_LOSS_USD}\n\nAll bots stopped.")
            
            stopped = stop_all_bots()
            state['stopped'] = True
            state['stop_time'] = datetime.now().isoformat()
            save_state(state)
            
            log(f"[STOPPED] {len(stopped)} bots halted")
            return False
        
        # CHECK 2: Position loss limit
        for pos in active_positions:
            if pos['pnl'] < -MAX_POSITION_LOSS_USD:
                log(f"🚨 POSITION LOSS LIMIT: {pos['symbol']} at ${pos['pnl']:.2f}")
                close_position(exchange, pos['symbol'], pos)
                send_alert(f"Position Closed\n\n{pos['symbol']} loss exceeded ${MAX_POSITION_LOSS_USD}\nPnL: ${pos['pnl']:.2f}")
        
        # CHECK 3: Minimum free balance
        if free_balance < MIN_FREE_BALANCE_USD:
            log(f"⚠️ LOW FREE BALANCE: ${free_balance:.2f} < ${MIN_FREE_BALANCE_USD}")
            send_alert(f"Margin Warning\n\nFree: ${free_balance:.2f}\nMin Required: ${MIN_FREE_BALANCE_USD}")
        
        # CHECK 4: Position size limits
        for pos in active_positions:
            position_value = pos['size'] * pos['entry']
            position_pct = (position_value / total_balance) * 100
            
            if position_pct > MAX_POSITION_SIZE_PCT:
                log(f"⚠️ POSITION OVERSIZED: {pos['symbol']} at {position_pct:.1f}%")
                # Don't close, just warn
                send_alert(f"Position Warning\n\n{pos['symbol']}: {position_pct:.1f}% of account\nMax: {MAX_POSITION_SIZE_PCT}%")
        
        log("[OK] All checks passed")
        log("=" * 60)
        return True
        
    except Exception as e:
        log(f"[CRITICAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run circuit breaker continuously"""
    log("\n" + "=" * 60)
    log("CIRCUIT BREAKER STARTED")
    log(f"Max Daily Loss: ${MAX_DAILY_LOSS_USD}")
    log(f"Max Position Loss: ${MAX_POSITION_LOSS_USD}")
    log(f"Min Free Balance: ${MIN_FREE_BALANCE_USD}")
    log("Checking every 60 seconds...")
    log("=" * 60 + "\n")
    
    try:
        while True:
            check_and_break()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        log("\n[STOPPED] Circuit breaker stopped by user")

if __name__ == '__main__':
    main()
