"""
Crypto.com Auto Trader v2 - Uses existing holdings
Sell when high, buy when low
"""
import os
import json
import requests
from datetime import datetime

os.environ['CDC_API_KEY'] = 'cdc_4c5aef5a38d7668ea5f249f1f68f'
os.environ['CDC_API_SECRET'] = 'EbwIHbqX30wEccOadwr+WBw7qUIJF0ClEXgBQVso+Sw='

SKILL_DIR = r'C:\Users\digim\.agents\skills\crypto-agent-trading'
TELEGRAM_BOT_TOKEN = '8249656817:AAFAI3oulkDWJZHJ7STSYlDfK-_UJCPo-7U'
TELEGRAM_CHAT_ID = '5804173449'

# Config - trade with existing holdings
SYMBOLS = ['LINK', 'ETH', 'CRO', 'XRP', 'DOGE']
SELL_THRESHOLD = 3  # % profit to sell
BUY_THRESHOLD = 4  # % dip to buy
NPX = r'C:\Program Files\nodejs\npx.cmd'

def send_alert(msg):
    try:
        requests.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
                     json={'chat_id': TELEGRAM_CHAT_ID, 'text': msg}, timeout=10)
    except:
        pass

def get_price(symbol):
    try:
        r = requests.get(f'https://api.crypto.com/v2/public/get-ticker?instrument_name={symbol}_USDT', timeout=10)
        data = r.json()
        return float(data['result']['data'][0]['a']), float(data['result']['data'][0]['h'])
    except:
        return None, None

def run_node(cmd):
    try:
        import subprocess
        result = subprocess.run(cmd, cwd=SKILL_DIR, capture_output=True, text=True, 
                              timeout=30, env=os.environ.copy())
        try:
            return json.loads(result.stdout.split('\n')[0])
        except:
            return None
    except:
        return None

def get_balance(symbol):
    result = run_node([NPX, 'tsx', 'scripts/account.ts', 'balance', symbol])
    if result and result.get('ok'):
        return float(result['data']['balance']['available'])
    return 0

def check_prices():
    print(f"[{datetime.now().strftime('%H:%M')}] Checking prices...")
    
    for symbol in SYMBOLS:
        price, high = get_price(symbol)
        if not price or not high:
            continue
        
        balance = get_balance(symbol)
        change = (price - high) / high * 100
        
        print(f"  {symbol}: ${price} (High: ${high}, Change: {change:.1f}%, Balance: {balance})")
        
        # Check if should sell (price up %)
        if change >= SELL_THRESHOLD and balance > 1:
            value_usd = balance * price
            print(f"    >>> Potential SELL opportunity!")
            send_alert(f"SELL SIGNAL: {symbol}\nPrice: ${price}\n24h High: ${high}\nChange: +{change:.1f}%\nBalance: {balance}")
        
        # Check if should buy (price down %)
        if change <= -BUY_THRESHOLD:
            print(f"    >>> Potential BUY opportunity!")
            send_alert(f"BUY SIGNAL: {symbol}\nPrice: ${price}\n24h High: ${high}\nChange: {change:.1f}%")

if __name__ == "__main__":
    print("="*50)
    print("Crypto.com Price Monitor v2")
    print("="*50)
    check_prices()
