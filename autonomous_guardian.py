"""
Agent33 Autonomous Guardian
Main autonomous decision engine for 100% hands-off trading management.

This script:
1. Monitors all positions and P&L
2. Makes autonomous decisions on position management
3. Opens new positions based on market conditions
4. Closes losers that exceed risk parameters
5. Scales winners
6. Flips bias when market conditions change
7. Sends Telegram alerts for all actions

Run every 5 minutes via cron for continuous autonomous operation.
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
import ccxt
import requests

# Load credentials
load_dotenv('.env.bybit')
BYBIT_API_KEY = os.getenv('BYBIT_API_KEY')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET')

# Telegram alerts
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_TELEGRAM_BOT_TOKEN_HERE')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID_HERE')

# Risk parameters
MAX_DAILY_LOSS_USDT = 50
MAX_POSITIONS = 6
POSITION_SIZE_USDT = 30
DEFAULT_TP_PCT = 0.025
DEFAULT_SL_PCT = 0.015

# Winner/banned symbols
WINNER_SYMBOLS = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 
                  'DOGE/USDT:USDT', 'XRP/USDT:USDT', 'NEAR/USDT:USDT']
BANNED_SYMBOLS = ['LINK/USDT:USDT', 'ADA/USDT:USDT', 'DOT/USDT:USDT',
                  'AVAX/USDT:USDT', 'LTC/USDT:USDT', 'BCH/USDT:USDT']

# State file for tracking decisions
STATE_FILE = 'autonomous_state.json'


def log(msg: str):
    """Log with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[AUTONOMOUS] {timestamp} - {msg}")


def send_telegram_alert(message: str):
    """Send alert to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        log(f"Telegram alert failed: {e}")


def get_exchange():
    """Initialize Bybit exchange"""
    try:
        exchange = ccxt.bybit({
            'apiKey': BYBIT_API_KEY,
            'secret': BYBIT_API_SECRET,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',
                'adjustForTimeDifference': True,
            }
        })
        exchange.set_sandbox_mode(False)
        return exchange
    except Exception as e:
        log(f"Exchange init error: {e}")
        return None


def load_state():
    """Load autonomous state"""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {
        'last_bias': None,
        'daily_pnl': 0,
        'last_reset': datetime.now().isoformat(),
        'positions_closed_today': 0,
        'positions_opened_today': 0
    }


def save_state(state):
    """Save autonomous state"""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        log(f"Failed to save state: {e}")


def check_positions(exchange):
    """Get current positions"""
    try:
        positions = exchange.fetch_positions()
        active = [p for p in positions if float(p.get('contracts', 0)) > 0]
        return active
    except Exception as e:
        log(f"Failed to fetch positions: {e}")
        return []


def calculate_portfolio_metrics(positions):
    """Calculate portfolio-level metrics"""
    total_pnl = sum(float(p.get('unrealisedPnl', 0)) for p in positions)
    total_margin = sum(float(p.get('initialMargin', 0)) for p in positions)
    
    # Check for banned symbols
    banned_found = [p for p in positions if any(b in p['symbol'] for b in BANNED_SYMBOLS)]
    
    # Check for underwater positions
    underwater = [p for p in positions if float(p.get('unrealisedPnl', 0)) < -5]
    
    return {
        'total_pnl': total_pnl,
        'total_margin': total_margin,
        'position_count': len(positions),
        'banned_symbols': banned_found,
        'underwater_positions': underwater
    }


def close_position(exchange, symbol: str, reason: str):
    """Close a position with alert"""
    try:
        log(f"AUTONOMOUS CLOSE: {symbol} - Reason: {reason}")
        
        # Close via market order
        order = exchange.create_market_sell_order(symbol, amount=0)  # 0 = close all
        
        alert = f"🚨 *AUTONOMOUS CLOSE*\n\n"
        alert += f"Symbol: `{symbol}`\n"
        alert += f"Reason: {reason}\n"
        alert += f"Time: {datetime.now().strftime('%H:%M:%S')} ET"
        
        send_telegram_alert(alert)
        return True
        
    except Exception as e:
        log(f"Failed to close {symbol}: {e}")
        return False


def open_position(exchange, symbol: str, side: str, size_usdt: float, reason: str):
    """Open a new position with TP/SL"""
    try:
        log(f"AUTONOMOUS OPEN: {symbol} {side} ${size_usdt} - Reason: {reason}")
        
        # Get current price
        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        
        # Calculate amount
        amount = size_usdt / price
        
        # Open position
        if side == 'LONG':
            order = exchange.create_market_buy_order(symbol, amount)
            tp_price = price * (1 + DEFAULT_TP_PCT)
            sl_price = price * (1 - DEFAULT_SL_PCT)
        else:
            order = exchange.create_market_sell_order(symbol, amount)
            tp_price = price * (1 - DEFAULT_TP_PCT)
            sl_price = price * (1 + DEFAULT_SL_PCT)
        
        # Set TP/SL
        exchange.private_post_v5_position_trading_stop({
            'category': 'linear',
            'symbol': symbol.replace('/', '').replace(':USDT', 'USDT'),
            'takeProfit': str(round(tp_price, 2)),
            'stopLoss': str(round(sl_price, 2)),
            'tpTriggerBy': 'LastPrice',
            'slTriggerBy': 'LastPrice',
            'tpTriggerDirection': 1 if side == 'LONG' else 2,
            'slTriggerDirection': 2 if side == 'LONG' else 1,
        })
        
        alert = f"🎯 *AUTONOMOUS ENTRY*\n\n"
        alert += f"Symbol: `{symbol}`\n"
        alert += f"Side: {side}\n"
        alert += f"Size: ${size_usdt:.2f}\n"
        alert += f"Entry: ${price:.2f}\n"
        alert += f"TP: ${tp_price:.2f} (+{DEFAULT_TP_PCT*100:.1f}%)\n"
        alert += f"SL: ${sl_price:.2f} (-{DEFAULT_SL_PCT*100:.1f}%)\n"
        alert += f"Reason: {reason}\n"
        alert += f"Time: {datetime.now().strftime('%H:%M:%S')} ET"
        
        send_telegram_alert(alert)
        return True
        
    except Exception as e:
        log(f"Failed to open {symbol}: {e}")
        return False


def get_market_bias():
    """Analyze market for bias (LONG/SHORT/NEUTRAL)"""
    try:
        # Check fear/greed index
        import urllib.request
        with urllib.request.urlopen('https://api.alternative.me/fng/') as response:
            data = json.loads(response.read())
            fear_greed = int(data['data'][0]['value'])
            
        if fear_greed <= 20:
            return 'LONG', f'Extreme fear ({fear_greed}/100)'
        elif fear_greed >= 80:
            return 'SHORT', f'Extreme greed ({fear_greed}/100)'
        else:
            return 'NEUTRAL', f'Neutral sentiment ({fear_greed}/100)'
            
    except Exception as e:
        log(f"Failed to get market bias: {e}")
        return 'NEUTRAL', 'Error fetching data'


def autonomous_decision_loop():
    """Main autonomous decision engine"""
    log("=" * 60)
    log("AGENT33 AUTONOMOUS GUARDIAN - Starting Cycle")
    log("=" * 60)
    
    # Load state
    state = load_state()
    
    # Check if we need to reset daily counters
    last_reset = datetime.fromisoformat(state['last_reset'])
    if (datetime.now() - last_reset).days >= 1:
        state['daily_pnl'] = 0
        state['positions_closed_today'] = 0
        state['positions_opened_today'] = 0
        state['last_reset'] = datetime.now().isoformat()
        log("Daily counters reset")
    
    # Connect to exchange
    exchange = get_exchange()
    if not exchange:
        log("ERROR: Could not connect to exchange")
        return
    
    # Get current positions
    positions = check_positions(exchange)
    metrics = calculate_portfolio_metrics(positions)
    
    log(f"Positions: {metrics['position_count']}/{MAX_POSITIONS}")
    log(f"Total Unrealized P&L: ${metrics['total_pnl']:.2f}")
    log(f"Daily P&L: ${state['daily_pnl']:.2f}")
    
    # DECISION 1: Close banned symbol positions immediately
    if metrics['banned_symbols']:
        for pos in metrics['banned_symbols']:
            symbol = pos['symbol']
            log(f"BANNED SYMBOL DETECTED: {symbol}")
            close_position(exchange, symbol, "Banned symbol - immediate exit")
            state['positions_closed_today'] += 1
    
    # DECISION 2: Close underwater positions >$5 loss
    for pos in metrics['underwater_positions']:
        symbol = pos['symbol']
        pnl = float(pos.get('unrealisedPnl', 0))
        log(f"UNDERWATER POSITION: {symbol} P&L: ${pnl:.2f}")
        close_position(exchange, symbol, f"Auto close - loss exceeded $5 (${pnl:.2f})")
        state['positions_closed_today'] += 1
    
    # DECISION 3: Check daily loss limit
    if state['daily_pnl'] < -MAX_DAILY_LOSS_USDT:
        log(f"DAILY LOSS LIMIT HIT: ${state['daily_pnl']:.2f} < -${MAX_DAILY_LOSS_USDT}")
        # Close worst position
        if positions:
            worst = min(positions, key=lambda p: float(p.get('unrealisedPnl', 0)))
            close_position(exchange, worst['symbol'], "Daily loss limit protection")
            state['positions_closed_today'] += 1
    
    # DECISION 4: Get market bias and potentially open new positions
    bias, reason = get_market_bias()
    log(f"Market Bias: {bias} - {reason}")
    
    # Check for bias flip
    if state['last_bias'] and state['last_bias'] != bias:
        log(f"BIAS FLIP DETECTED: {state['last_bias']} -> {bias}")
        
        # Close opposite positions
        if bias == 'LONG':
            for pos in positions:
                if pos['side'] == 'short':
                    close_position(exchange, pos['symbol'], f"Bias flip to {bias}")
                    state['positions_closed_today'] += 1
        elif bias == 'SHORT':
            for pos in positions:
                if pos['side'] == 'long':
                    close_position(exchange, pos['symbol'], f"Bias flip to {bias}")
                    state['positions_closed_today'] += 1
        
        # Send bias flip alert
        alert = f"🔄 *BIAS FLIP: {bias}*\n\n"
        alert += f"Previous: {state['last_bias']}\n"
        alert += f"Current: {bias}\n"
        alert += f"Reason: {reason}\n"
        alert += f"Time: {datetime.now().strftime('%H:%M:%S')} ET"
        send_telegram_alert(alert)
    
    state['last_bias'] = bias
    
    # DECISION 5: Open new positions if conditions met
    if bias in ['LONG', 'SHORT'] and metrics['position_count'] < MAX_POSITIONS:
        # Find symbols we don't have positions in
        current_symbols = {p['symbol'] for p in positions}
        available = [s for s in WINNER_SYMBOLS if s not in current_symbols]
        
        if available:
            # Open position on first available symbol
            symbol = available[0]
            side = 'LONG' if bias == 'LONG' else 'SHORT'
            
            open_position(exchange, symbol, side, POSITION_SIZE_USDT, 
                         f"Autonomous entry - {bias} bias ({reason})")
            state['positions_opened_today'] += 1
    
    # Save state
    save_state(state)
    
    log("=" * 60)
    log("Autonomous cycle complete")
    log(f"Positions opened today: {state['positions_opened_today']}")
    log(f"Positions closed today: {state['positions_closed_today']}")
    log("=" * 60)


if __name__ == "__main__":
    try:
        autonomous_decision_loop()
    except Exception as e:
        log(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
