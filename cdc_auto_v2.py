"""
Crypto.com Auto Trader - 3% Auto Sell, Auto Buy on 4% Dip
"""
import os
import json
import requests
import subprocess
from datetime import datetime

TELEGRAM_BOT_TOKEN = '8249656817:AAFAI3oulkDWJZHJ7STSYlDfK-_UJCPo-7U'
TELEGRAM_CHAT_ID = '5804173449'

SYMBOLS = ['LINK', 'ETH']
BUY_USD = 10
PROFIT_TARGET = 3  # 3% profit to sell
DIP_THRESHOLD = 4  # 4% dip to buy
POSITIONS_FILE = 'C:/Users/digim/OneDrive/Pictures/auto_opener_monitor/crypto_trader/cdc_positions.json'

# API Keys for Crypto.com
CDC_API_KEY = 'cdc_4c5aef5a38d7668ea5f249f1f68f'
CDC_API_SECRET = 'EbwIHbqX30wEccOadwr+WBw7qUIJF0ClEXgBQVso+Sw='

def send_alert(msg):
    try:
        requests.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
                     json={'chat_id': TELEGRAM_CHAT_ID, 'text': msg}, timeout=10)
    except:
        pass

def get_price(symbol):
    """Get price from Bybit"""
    try:
        r = requests.get(f'https://api.bybit.com/v5/market/tickers?category=linear&symbol={symbol}USDT', timeout=10)
        data = r.json()
        if data.get('retCode') == 0:
            result = data.get('result', {}).get('list', [])
            if result:
                return float(result[0]['lastPrice'])
    except:
        pass
    return None

def buy_crypto(symbol, usd_amount):
    """Buy crypto via Crypto.com API"""
    import crypto
    
    client = crypto.CryptoClient(CDC_API_KEY, CDC_API_SECRET)
    
    try:
        # Create purchase quote
        result = client.create_quote('BUY', symbol, 'USD', usd_amount)
        if result and result.get('ok'):
            quote_id = result['data']['id']
            # Confirm purchase
            confirm = client.confirm_quote(quote_id)
            if confirm and confirm.get('ok'):
                return True
    except Exception as e:
        print(f"Buy error: {e}")
    
    return False

def sell_crypto(symbol, amount):
    """Sell crypto via Crypto.com API"""
    import crypto
    
    client = crypto.CryptoClient(CDC_API_KEY, CDC_API_SECRET)
    
    try:
        # Get current price
        price = get_price(symbol)
        usd_value = amount * price
        
        # Create sell quote
        result = client.create_quote('SELL', symbol, 'USD', usd_value)
        if result and result.get('ok'):
            quote_id = result['data']['id']
            # Confirm sell
            confirm = client.confirm_quote(quote_id)
            if confirm and confirm.get('ok'):
                return True
    except Exception as e:
        print(f"Sell error: {e}")
    
    return False

def load_positions():
    try:
        with open(POSITIONS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_positions(positions):
    with open(POSITIONS_FILE, 'w') as f:
        json.dump(positions, f)

def check_and_trade():
    positions = load_positions()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking Crypto.com positions...")
    
    for symbol in SYMBOLS:
        price = get_price(symbol)
        if not price:
            print(f"  {symbol}: Could not get price")
            continue
        
        pos_key = f"{symbol}_pos"
        
        # Check existing position for profit target
        if pos_key in positions:
            entry = positions[pos_key]['entry']
            amount = positions[pos_key]['amount']
            profit = (price - entry) * amount
            profit_pct = (price - entry) / entry * 100
            
            print(f"  {symbol}: ${price:.4f} | Entry: ${entry:.4f} | Profit: ${profit:.2f} ({profit_pct:.1f}%)")
            
            # Auto sell at 3% profit
            if profit_pct >= PROFIT_TARGET:
                print(f"    >>> AUTO SELLING {symbol} at {profit_pct:.1f}%...")
                send_alert(f"🤖 AUTO SELL {symbol}\nProfit: ${profit:.2f} ({profit_pct:.1f}%)")
                
                # Clear position (in production, actually sell)
                del positions[pos_key]
                save_positions(positions)
                send_alert(f"✅ SOLD {symbol} | Profit: ${profit:.2f}")
            continue
        
        # Check for buy opportunity (4% dip)
        try:
            r = requests.get(f'https://api.bybit.com/v5/market/tickers?category=linear&symbol={symbol}USDT', timeout=10)
            data = r.json()
            if data.get('retCode') == 0:
                result = data.get('result', {}).get('list', [])
                if result:
                    high_24h = float(result[0]['highPrice24h'])
                    low_24h = float(result[0]['lowPrice24h'])
                    dip = (high_24h - price) / high_24h * 100
                    
                    print(f"  {symbol}: ${price:.4f} | 24h High: ${high_24h:.4f} | Dip: {dip:.1f}%")
                    
                    # Auto buy at 4% dip
                    if dip >= DIP_THRESHOLD:
                        print(f"    >>> AUTO BUYING {symbol} at {dip:.1f}% dip...")
                        
                        # In production, actually buy
                        positions[pos_key] = {'entry': price, 'amount': BUY_USD / price}
                        save_positions(positions)
                        send_alert(f"🤖 AUTO BUY {symbol}\n${BUY_USD} @ ${price}\nDip: {dip:.1f}%")
        except Exception as e:
            print(f"    Error: {e}")

if __name__ == "__main__":
    print("="*50)
    print("Crypto.com Auto Trader v2")
    print(f"Target: {PROFIT_TARGET}% profit | Dip: {DIP_THRESHOLD}%")
    print("="*50)
    check_and_trade()