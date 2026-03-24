"""
Crypto.com Auto Trader - WORKING VERSION
"""
import os
import json
import requests
import subprocess
import hmac
import hashlib
import base64
import time
from datetime import datetime

API_KEY = 'cdc_4c5aef5a38d7668ea5f249f1f68f'
API_SECRET = 'EbwIHbqX30wEccOadwr+WBw7qUIJF0ClEXgBQVso+Sw='
TELEGRAM_BOT_TOKEN = '8249656817:AAFAI3oulkDWJZHJ7STSYlDfK-_UJCPo-7U'
TELEGRAM_CHAT_ID = '5804173449'

SYMBOLS = ['LINK', 'ETH']
BUY_USD = 10
PROFIT_PCT = 5
POSITIONS_FILE = 'C:/Users/digim/OneDrive/Pictures/auto_opener_monitor/crypto_trader/cdc_positions.json'

def send_alert(msg):
    try:
        requests.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
                     json={'chat_id': TELEGRAM_CHAT_ID, 'text': msg}, timeout=10)
    except:
        pass

def get_price(symbol):
    try:
        r = requests.get(f'https://api.crypto.com/v2/public/get-ticker?instrument_name={symbol}_USDT', timeout=10)
        return float(r.json()['result']['data'][0]['a'])
    except:
        return None

def buy_crypto(symbol, usd_amount):
    try:
        # Get quote
        ts = str(int(time.time() * 1000))
        body = {'from_currency': 'USD', 'to_currency': symbol, 'to_amount': usd_amount}
        body_str = json.dumps(body)
        
        # Sign correctly
        sign_payload = ts + 'POST' + '/v1/crypto-purchase/quotations' + body_str
        sig = hmac.new(API_SECRET.encode(), sign_payload.encode(), hashlib.sha256)
        signature = base64.b64encode(sig.digest()).decode()
        
        headers = {'Content-Type': 'application/json', 'Cdc-Api-Key': API_KEY, 'Cdc-Api-Timestamp': ts, 'Cdc-Api-Signature': signature}
        
        r = requests.post('https://wapi.crypto.com/v1/crypto-purchase/quotations', json=body, headers=headers)
        quote = r.json()
        
        if not quote.get('ok'):
            print(f"Quote failed: {quote.get('error')}")
            return False
        
        quote_id = quote['quotation']['id']
        print(f"Got quote: {quote_id}")
        
        # Execute immediately
        ts2 = str(int(time.time() * 1000))
        body2 = {'quotation_id': quote_id}
        body_str2 = json.dumps(body2)
        sign_payload2 = ts2 + 'POST' + '/v1/crypto-purchase/orders' + body_str2
        signature2 = base64.b64encode(hmac.new(API_SECRET.encode(), sign_payload2.encode(), hashlib.sha256).digest()).decode()
        
        headers2 = {'Content-Type': 'application/json', 'Cdc-Api-Key': API_KEY, 'Cdc-Api-Timestamp': ts2, 'Cdc-Api-Signature': signature2}
        
        r2 = requests.post('https://wapi.crypto.com/v1/crypto-purchase/orders', json=body2, headers=headers2)
        result = r2.json()
        
        if result.get('ok'):
            print(f"Successfully bought {symbol}!")
            return True
        else:
            print(f"Buy failed: {result}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
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
    print(f"[{datetime.now().strftime('%H:%M')}] Checking...")
    
    for symbol in SYMBOLS:
        price = get_price(symbol)
        if not price:
            continue
        
        pos_key = f"{symbol}_pos"
        
        if pos_key in positions:
            entry = positions[pos_key]['entry']
            amount = positions[pos_key]['amount']
            profit = (price - entry) * amount
            profit_pct = (price - entry) / entry * 100
            
            print(f"  {symbol}: ${price} (Entry: ${entry}, Profit: ${profit:.2f} / {profit_pct:.1f}%)")
            
            if profit_pct >= PROFIT_PCT:
                send_alert(f"SELL {symbol}\nProfit: ${profit:.2f} ({profit_pct:.1f}%)")
                del positions[pos_key]
                save_positions(positions)
            continue
        
        try:
            r = requests.get(f'https://api.crypto.com/v2/public/get-ticker?instrument_name={symbol}_USDT', timeout=10)
            high = float(r.json()['result']['data'][0]['h'])
            dip = (high - price) / high * 100
            
            print(f"  {symbol}: ${price} (High: ${high}, Dip: {dip:.1f}%)")
            
            if dip >= 4:
                print(f"    >>> BUYING {symbol}...")
                if buy_crypto(symbol, BUY_USD):
                    amount = BUY_USD / price
                    positions[pos_key] = {'entry': price, 'amount': amount}
                    save_positions(positions)
                    send_alert(f"BOUGHT {symbol}\n${BUY_USD} @ ${price}")
                    print(f"    >>> BOUGHT!")
        except Exception as e:
            print(f"    Error: {e}")

if __name__ == "__main__":
    print("="*50)
    print("Crypto.com Auto Trader - WORKING!")
    print("="*50)
    check_and_trade()
