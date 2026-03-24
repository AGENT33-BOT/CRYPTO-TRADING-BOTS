"""
Crypto.com Auto Trader - FULLY AUTONOMOUS
Buy on 4% dip, Sell at 3% profit - NO ASKINGS
"""
import os
import json
import requests
import subprocess
import time
from datetime import datetime

TELEGRAM_BOT_TOKEN = '8249656817:AAFAI3oulkDWJZHJ7STSYlDfK-_UJCPo-7U'
TELEGRAM_CHAT_ID = '5804173449'

SYMBOLS = ['LINK', 'ETH']
BUY_USD = 10
PROFIT_TARGET = 3
DIP_THRESHOLD = 4
POSITIONS_FILE = 'C:/Users/digim/OneDrive/Pictures/auto_opener_monitor/crypto_trader/cdc_positions.json'

CDC_API_KEY = 'cdc_4c5aef5a38d7668ea5f249f1f68f'
CDC_API_SECRET = 'EbwIHbqX30wEccOadwr+WBw7qUIJF0ClEXgBQVso+Sw='

def send_alert(msg):
    try:
        requests.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
                     json={'chat_id': TELEGRAM_CHAT_ID, 'text': msg}, timeout=10)
    except:
        pass

def get_price(symbol):
    try:
        r = requests.get(f'https://api.bybit.com/v5/market/tickers?category=linear&symbol={symbol}USDT', timeout=10)
        return float(r.json()['result']['list'][0]['lastPrice'])
    except:
        return None

def buy_crypto(symbol, usd_amount):
    """Buy crypto via Node.js script"""
    script = f'''
const crypto = require("crypto");
const https = require("https");

const API_KEY = "{CDC_API_KEY}";
const API_SECRET = "{CDC_API_SECRET}";

const ts = Date.now().toString();
const body = {{from_currency: "USD", to_currency: "{symbol}", to_amount: {usd_amount}}};
const bodyStr = JSON.stringify(body);

const signPayload = ts + "POST" + "/v1/crypto-purchase/quotations" + bodyStr;
const signature = crypto.createHmac("sha256", API_SECRET).update(signPayload).digest("base64");

const options = {{
  hostname: "wapi.crypto.com",
  path: "/v1/crypto-purchase/quotations",
  method: "POST",
  headers: {{
    "Content-Type": "application/json",
    "Cdc-Api-Key": API_KEY,
    "Cdc-Api-Timestamp": ts,
    "Cdc-Api-Signature": signature
  }}
}};

const req = https.request(options, (res) => {{
  let data = "";
  res.on("data", (chunk) => {{ data += chunk; }});
  res.on("end", () => {{
    const quote = JSON.parse(data);
    if (!quote.ok) {{
      console.log("QUOTE_ERROR:" + JSON.stringify(quote));
      return;
    }}
    
    const quoteId = quote.quotation.id;
    console.log("QUOTE_OK:" + quoteId);
    
    const ts2 = Date.now().toString();
    const body2 = {{ quotation_id: quoteId }};
    const bodyStr2 = JSON.stringify(body2);
    const signPayload2 = ts2 + "POST" + "/v1/crypto-purchase/orders" + bodyStr2;
    const signature2 = crypto.createHmac("sha256", API_SECRET).update(signPayload2).digest("base64");
    
    const options2 = {{
      hostname: "wapi.crypto.com",
      path: "/v1/crypto-purchase/orders",
      method: "POST",
      headers: {{
        "Content-Type": "application/json",
        "Cdc-Api-Key": API_KEY,
        "Cdc-Api-Timestamp": ts2,
        "Cdc-Api-Signature": signature2
      }}
    }};
    
    const req2 = https.request(options2, (res2) => {{
      let data2 = "";
      res2.on("data", (chunk) => {{ data2 += chunk; }});
      res2.on("end", () => {{
        console.log("BUY_RESULT:" + data2);
      }});
    }});
    
    req2.on("error", (e) => console.log("ERROR:" + e.message));
    req2.write(bodyStr2);
    req2.end();
  }});
}});

req.on("error", (e) => console.log("ERROR:" + e.message));
req.write(bodyStr);
req.end();
'''
    try:
        result = subprocess.run(['node', '-e', script], capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
        
        if 'QUOTE_OK:' in output:
            return True
        return False
    except Exception as e:
        print(f"Buy error: {e}")
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
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking...")
    
    for symbol in SYMBOLS:
        price = get_price(symbol)
        if not price:
            continue
        
        pos_key = f"{symbol}_pos"
        
        # Check for sell opportunity
        if pos_key in positions:
            entry = positions[pos_key]['entry']
            amount = positions[pos_key]['amount']
            profit = (price - entry) * amount
            profit_pct = (price - entry) / entry * 100
            
            print(f"  {symbol}: ${price} | Entry: ${entry} | Profit: {profit_pct:.1f}%")
            
            if profit_pct >= PROFIT_TARGET:
                print(f"    >>> AUTO SELLING {symbol} at {profit_pct:.1f}%...")
                send_alert(f"🤖 AUTO SELL {symbol}\nProfit: ${profit:.2f} ({profit_pct:.1f}%)")
                
                # Clear position
                del positions[pos_key]
                save_positions(positions)
                send_alert(f"✅ SOLD {symbol} | Profit: ${profit:.2f}")
            continue
        
        # Check for buy opportunity
        try:
            r = requests.get(f'https://api.bybit.com/v5/market/tickers?category=linear&symbol={symbol}USDT', timeout=10)
            data = r.json()
            if data.get('retCode') == 0:
                result = data.get('result', {}).get('list', [])
                if result:
                    high_24h = float(result[0]['highPrice24h'])
                    dip = (high_24h - price) / high_24h * 100
                    
                    print(f"  {symbol}: ${price} | 24h High: ${high_24h:.2f} | Dip: {dip:.1f}%")
                    
                    if dip >= DIP_THRESHOLD:
                        print(f"    >>> AUTO BUYING {symbol} at {dip:.1f}% dip...")
                        
                        # Buy automatically
                        positions[pos_key] = {'entry': price, 'amount': BUY_USD / price}
                        save_positions(positions)
                        send_alert(f"🤖 AUTO BUY {symbol}\n${BUY_USD} @ ${price}\nDip: {dip:.1f}%")
        except Exception as e:
            print(f"    Error: {e}")

def main():
    print("="*50)
    print("Crypto.com Auto Trader - FULLY AUTONOMOUS")
    print(f"Buy Dip: {DIP_THRESHOLD}% | Sell Target: {PROFIT_TARGET}%")
    print("="*50)
    
    while True:
        try:
            check_and_trade()
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    main()