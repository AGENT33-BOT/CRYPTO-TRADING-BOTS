"""
Crypto.com Auto Trader - Uses working Node.js
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
    """Use Node.js to buy"""
    try:
        script = f"""
const crypto = require('crypto');
const https = require('https');

const API_KEY = 'cdc_4c5aef5a38d7668ea5f249f1f68f';
const API_SECRET = 'EbwIHbqX30wEccOadwr+WBw7qUIJF0ClEXgBQVso+Sw=';

const ts = Date.now().toString();
const method = 'POST';
const path = '/v1/crypto-purchase/quotations';

const body = {{from_currency: 'USD', to_currency: '{symbol}', to_amount: {usd_amount}}};
const bodyStr = JSON.stringify(body);
const signPayload = ts + method + path + bodyStr;

const signature = crypto.createHmac('sha256', API_SECRET).update(signPayload).digest('base64');

const options = {{
  hostname: 'wapi.crypto.com',
  path: path,
  method: method,
  headers: {{
    'Content-Type': 'application/json',
    'Cdc-Api-Key': API_KEY,
    'Cdc-Api-Timestamp': ts,
    'Cdc-Api-Signature': signature
  }}
}};

const req = https.request(options, (res) => {{
  let data = '';
  res.on('data', (chunk) => {{ data += chunk; }});
  res.on('end', () => {{
    const quote = JSON.parse(data);
    if (!quote.ok) {{
      console.log('QUOTE_ERROR:' + JSON.stringify(quote));
      return;
    }}
    
    const quoteId = quote.quotation.id;
    console.log('QUOTE:' + quoteId);
    
    // Execute immediately
    const ts2 = Date.now().toString();
    const body2 = {{ quotation_id: quoteId }};
    const bodyStr2 = JSON.stringify(body2);
    const signPayload2 = ts2 + method + '/v1/crypto-purchase/orders' + bodyStr2;
    const signature2 = crypto.createHmac('sha256', API_SECRET).update(signPayload2).digest('base64');
    
    const options2 = {{
      hostname: 'wapi.crypto.com',
      path: '/v1/crypto-purchase/orders',
      method: method,
      headers: {{
        'Content-Type': 'application/json',
        'Cdc-Api-Key': API_KEY,
        'Cdc-Api-Timestamp': ts2,
        'Cdc-Api-Signature': signature2
      }}
    }};
    
    const req2 = https.request(options2, (res2) => {{
      let data2 = '';
      res2.on('data', (chunk) => {{ data2 += chunk; }});
      res2.on('end', () => {{
        console.log('BUY_RESULT:' + data2);
      }});
    }});
    
    req2.on('error', (e) => console.log('ERROR:' + e.message));
    req2.write(bodyStr2);
    req2.end();
  }});
}});

req.on('error', (e) => console.log('ERROR:' + e.message));
req.write(bodyStr);
req.end();
"""
        result = subprocess.run(['node', '-e', script], capture_output=True, text=True, timeout=30)
        
        output = result.stdout + result.stderr
        
        if 'QUOTE:' in output:
            print(f"Bought {symbol}!")
            return True
        elif 'QUOTE_ERROR' in output:
            print(f"Quote error: {output}")
            return False
        else:
            print(f"Output: {output}")
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
        except Exception as e:
            print(f"    Error: {e}")

if __name__ == "__main__":
    print("="*50)
    print("Crypto.com Auto Trader")
    print("="*50)
    check_and_trade()
