"""
Flip Bias Script
Changes trading bias from LONG to SHORT or vice versa.
Closes opposite positions and optionally opens new ones.
"""

import argparse
from datetime import datetime

import ccxt
from dotenv import load_dotenv
import os

load_dotenv('.env.bybit')

BYBIT_API_KEY = os.getenv('BYBIT_API_KEY')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET')

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

WINNER_SYMBOLS = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT',
                  'DOGE/USDT:USDT', 'XRP/USDT:USDT', 'NEAR/USDT:USDT']


def send_alert(message: str):
    """Send Telegram alert"""
    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Alert failed: {e}")


def get_exchange():
    """Initialize exchange"""
    return ccxt.bybit({
        'apiKey': BYBIT_API_KEY,
        'secret': BYBIT_API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })


def close_opposite_positions(exchange, new_bias: str):
    """Close positions opposite to new bias"""
    positions = exchange.fetch_positions()
    active = [p for p in positions if float(p.get('contracts', 0)) > 0]
    
    closed = []
    
    for pos in active:
        symbol = pos['symbol']
        side = pos['side']
        size = float(pos.get('contracts', 0))
        
        # Close if opposite to new bias
        if (new_bias == 'LONG' and side == 'short') or \
           (new_bias == 'SHORT' and side == 'long'):
            
            try:
                if side == 'long':
                    exchange.create_market_sell_order(symbol, size)
                else:
                    exchange.create_market_buy_order(symbol, size)
                
                closed.append(f"{symbol} ({side})")
                print(f"✅ Closed opposite: {symbol} ({side})")
                
            except Exception as e:
                print(f"❌ Failed to close {symbol}: {e}")
    
    return closed


def open_bias_positions(exchange, bias: str, count: int = 2):
    """Open new positions aligned with bias"""
    positions = exchange.fetch_positions()
    current_symbols = {p['symbol'] for p in positions if float(p.get('contracts', 0)) > 0}
    
    available = [s for s in WINNER_SYMBOLS if s not in current_symbols][:count]
    opened = []
    
    for symbol in available:
        try:
            ticker = exchange.fetch_ticker(symbol)
            price = ticker['last']
            size_usdt = 30
            amount = size_usdt / price
            
            if bias == 'LONG':
                exchange.create_market_buy_order(symbol, amount)
                tp = price * 1.025
                sl = price * 0.985
            else:
                exchange.create_market_sell_order(symbol, amount)
                tp = price * 0.975
                sl = price * 1.015
            
            # Set TP/SL
            exchange.private_post_v5_position_trading_stop({
                'category': 'linear',
                'symbol': symbol.replace('/', '').replace(':USDT', 'USDT'),
                'takeProfit': str(round(tp, 2)),
                'stopLoss': str(round(sl, 2)),
                'tpTriggerBy': 'LastPrice',
                'slTriggerBy': 'LastPrice',
            })
            
            opened.append(f"{symbol} {bias}")
            print(f"✅ Opened: {symbol} {bias}")
            
        except Exception as e:
            print(f"❌ Failed to open {symbol}: {e}")
    
    return opened


def flip_bias(direction: str, reason: str, open_new: bool = True):
    """Main flip logic"""
    print("=" * 60)
    print(f"🔄 FLIPPING BIAS TO: {direction}")
    print(f"Reason: {reason}")
    print("=" * 60)
    
    exchange = get_exchange()
    
    # Step 1: Close opposite positions
    print("\n📤 Closing opposite positions...")
    closed = close_opposite_positions(exchange, direction)
    
    # Step 2: Open new positions (if requested)
    opened = []
    if open_new:
        print(f"\n📥 Opening {direction} positions...")
        opened = open_bias_positions(exchange, direction)
    
    # Send alert
    alert = f"🔄 *BIAS FLIP: {direction}*\n\n"
    alert += f"Reason: {reason}\n"
    alert += f"Time: {datetime.now().strftime('%H:%M:%S')} ET\n\n"
    
    if closed:
        alert += f"*Closed Opposite:*\n" + "\n".join([f"🔴 {c}" for c in closed]) + "\n\n"
    
    if opened:
        alert += f"*Opened {direction}:*\n" + "\n".join([f"🟢 {o}" for o in opened])
    
    send_alert(alert)
    
    print("\n" + "=" * 60)
    print(f"Flip complete. Closed: {len(closed)}, Opened: {len(opened)}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='Flip Trading Bias')
    parser.add_argument('--direction', type=str, required=True, 
                       choices=['LONG', 'SHORT'], help='New bias direction')
    parser.add_argument('--reason', type=str, required=True,
                       help='Reason for flip (e.g., "extreme_fear_12/100")')
    parser.add_argument('--no-open', action='store_true',
                       help='Only close opposite, do not open new positions')
    
    args = parser.parse_args()
    
    flip_bias(args.direction, args.reason, not args.no_open)


if __name__ == "__main__":
    main()
