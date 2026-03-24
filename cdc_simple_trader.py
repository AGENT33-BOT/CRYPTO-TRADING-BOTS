"""
Crypto.com Auto Trader - Simplified
Buy on dip, sell at profit
"""
import os
import json
import time
import hmac
import hashlib
import requests
from datetime import datetime

# API Keys
API_KEY = 'cdc_14e0bf120eb9fd8d3316997344a2'
API_SECRET = 'LOee9CovN2KmQylkI3/36QQDvrh6pg4PYl0TLzBgC18='

TELEGRAM_BOT_TOKEN = '8249656817:AAFAI3oulkDWJZHJ7STSYlDfK-_UJCPo-7U'
TELEGRAM_CHAT_ID = '5804173449'

# Config
SYMBOLS = ['LINK', 'ETH']
BUY_AMOUNT = 10  # USD
SELL_PROFIT = 5   # USD profit target
POSITIONS_FILE = 'C:/Users/digim/OneDrive/Pictures/auto_opener_monitor/crypto_trader/cdc_positions.json'

def send_alert(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=10)
    except:
        pass

def sign_request(params):
    """Sign request for Crypto.com API"""
    sorted_params = sorted(params.items())
    param_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
    signature = hmac.new(
        API_SECRET.encode(),
        param_str.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

def api_request(method, params=None):
    """Make API request"""
    if params is None:
        params = {}
    
    params['api_key'] = API_KEY
    params['timestamp'] = str(int(time.time() * 1000))
    
    # Sign
    sorted_params = sorted(params.items())
    param_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
    signature = hmac.new(
        API_SECRET.encode(),
        param_str.encode(),
        hashlib.sha256
    ).hexdigest()
    params['sig'] = signature
    
    url = f"https://api.crypto.com/v2/{method}"
    r = requests.post(url, json=params, timeout=10)
    return r.json()

def get_price(symbol):
    """Get current price"""
    try:
        r = requests.get(f"https://api.crypto.com/v2/public/get-ticker?instrument_name={symbol}_USDT", timeout=10)
        data = r.json()
        if data.get('code') == 0:
            return float(data['result']['data'][0]['a'])
    except:
        pass
    return None

def get_balance(symbol):
    """Get crypto balance"""
    result = api_request('private/get-balance', {'currency': symbol})
    if result.get('code') == 0:
        return float(result['result']['data']['balance']['available'])
    return 0

def buy_crypto(symbol, usd_amount):
    """Buy crypto"""
    # First get current price to calculate amount
    price = get_price(symbol)
    if not price:
        return False
    
    amount = usd_amount / price
    
    # Create order
    params = {
        'side': 'BUY',
        'symbol': f'{symbol}_USDT',
        'type': 'MARKET',
        'quantity': str(amount),
        'time_in_force': 'IOC'
    }
    
    result = api_request('private/create-order', params)
    
    if result.get('code') == 0:
        return True
    else:
        print(f"Buy error: {result}")
        return False

def sell_crypto(symbol, amount):
    """Sell crypto"""
    params = {
        'side': 'SELL',
        'symbol': f'{symbol}_USDT',
        'type': 'MARKET',
        'quantity': str(amount),
        'time_in_force': 'IOC'
    }
    
    result = api_request('private/create-order', params)
    
    if result.get('code') == 0:
        return True
    else:
        print(f"Sell error: {result}")
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
    """Main trading logic"""
    positions = load_positions()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking...")
    
    for symbol in SYMBOLS:
        try:
            current_price = get_price(symbol)
            if not current_price:
                continue
            
            pos_key = f"{symbol}_position"
            
            # Check position
            if pos_key in positions:
                entry_price = positions[pos_key]['entry_price']
                amount = positions[pos_key]['amount']
                profit = (current_price - entry_price) * amount
                
                print(f"  {symbol}: ${current_price} (Entry: ${entry_price}, Profit: ${profit:.2f})")
                
                if profit >= SELL_PROFIT:
                    if sell_crypto(symbol, amount):
                        msg = f"SOLD {symbol}\nProfit: ${profit:.2f}"
                        print(f"  >>> {msg}")
                        send_alert(msg)
                        del positions[pos_key]
                        save_positions(positions)
                continue
            
            # Buy opportunity check
            r = requests.get(f"https://api.crypto.com/v2/public/get-ticker?instrument_name={symbol}_USDT", timeout=10)
            data = r.json()
            high_24h = float(data['result']['data'][0]['h'])
            
            dip_pct = (high_24h - current_price) / high_24h * 100
            print(f"  {symbol}: ${current_price} (High: ${high_24h}, Down: {dip_pct:.1f}%)")
            
            if dip_pct >= 4:
                print(f"  >>> BUYING {symbol}...")
                if buy_crypto(symbol, BUY_AMOUNT):
                    amount = BUY_AMOUNT / current_price
                    positions[pos_key] = {
                        'entry_price': current_price,
                        'amount': amount
                    }
                    save_positions(positions)
                    msg = f"BOUGHT {symbol}\n${BUY_AMOUNT} @ ${current_price}"
                    print(f"  >>> {msg}")
                    send_alert(msg)
                    
        except Exception as e:
            print(f"Error {symbol}: {e}")
    
    print()

if __name__ == "__main__":
    print("="*50)
    print("Crypto.com Auto Trader")
    print("="*50)
    check_and_trade()
