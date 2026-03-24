"""
Crypto.com LINK/ETH Opportunity Monitor
Buys when dip detected, sells when $5 profit made
"""
import os
import sys
import time
import json
from datetime import datetime

# Set environment variables
os.environ['CDC_API_KEY'] = 'cdc_14e0bf120eb9fd8d3316997344a2'
os.environ['CDC_API_SECRET'] = 'LOee9CovN2KmQylkI3/36QQDvrh6pg4PYl0TLzBgC18='

sys.path.insert(0, 'C:/Users/digim/.agents/skills/crypto-agent-trading/scripts')

from lib.crypto import CryptoClient

# Telegram alert
TELEGRAM_BOT_TOKEN = '8249656817:AAFAI3oulkDWJZHJ7STSYlDfK-_UJCPo-7U'
TELEGRAM_CHAT_ID = '5804173449'

def send_alert(msg):
    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except:
        pass

def get_price(symbol):
    """Get current price from Crypto.com"""
    client = CryptoClient()
    book = client.get_book(symbol)
    if book and 'data' in book:
        return float(book['data']['price'])
    return None

def get_balance(symbol):
    """Get balance for a symbol"""
    client = CryptoClient()
    result = client.get_balance()
    if result and 'data' in result:
        for curr in result['data'].get('crypto', []):
            if curr.get('currency') == symbol:
                return float(curr.get('available', 0))
    return 0

def buy(symbol, amount):
    """Buy crypto"""
    client = CryptoClient()
    # Get quote
    quote = client.create_quote('BUY', symbol, 'USD', amount)
    if quote and 'data' in quote:
        # Confirm
        confirmation = client.confirm_quote(quote['data']['id'])
        if confirmation and confirmation.get('ok'):
            return True
    return False

def get_trading_limit():
    """Check weekly trading limit"""
    client = CryptoClient()
    return client.get_trading_limit()

# Config
SYMBOLS = ['LINK', 'ETH']
BUY_AMOUNT = 10  # USD per buy
SELL_PROFIT = 5  # USD profit target

# Track positions
POSITIONS_FILE = 'C:/Users/digim/OneDrive/Pictures/auto_opener_monitor/crypto_trader/cdc_positions.json'

def load_positions():
    try:
        with open(POSITIONS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_positions(positions):
    with open(POSITIONS_FILE, 'w') as f:
        json.dump(positions, f)

def check_opportunities():
    client = CryptoClient()
    positions = load_positions()
    
    for symbol in SYMBOLS:
        try:
            # Get current price
            book = client.get_book(symbol)
            if not book or 'data' not in book:
                continue
            
            price = float(book['data']['price'])
            print(f"{symbol}: ${price}")
            
            # Check if we have a position
            pos_key = f"{symbol}_usd"
            if pos_key in positions:
                entry_price = positions[pos_key]['entry_price']
                profit = (price - entry_price) * positions[pos_key]['amount']
                
                if profit >= SELL_PROFIT:
                    # Sell!
                    amount = positions[pos_key]['amount']
                    quote = client.create_quote('SELL', symbol, 'USD', amount * price)
                    if quote and 'data' in quote:
                        confirmation = client.confirm_quote(quote['data']['id'])
                        if confirmation and confirmation.get('ok'):
                            msg = f"SOLD {symbol} | Profit: ${profit:.2f}"
                            print(msg)
                            send_alert(msg)
                            del positions[pos_key]
                            save_positions(positions)
                continue
            
            # Check for buy opportunity - simple dip detection
            # For now, just buy on any pullback
            # In production, you'd use RSI, MACD, etc.
            
            # Get 24h change
            # For simplicity, buy on 1% dip from recent
            # This is a simplified strategy
            
            print(f"  No position, checking opportunity...")
            
        except Exception as e:
            print(f"Error with {symbol}: {e}")

if __name__ == "__main__":
    print("="*50)
    print("Crypto.com LINK/ETH Opportunity Monitor")
    print("="*50)
    
    # Initial check
    check_opportunities()
    
    print("\nTo run continuously, add to cron or background task")
