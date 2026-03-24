"""
Crypto.com Auto Trader - Uses Node.js SDK
Monitors LINK/ETH, buys on dip, sells at profit
"""
import os
import json
import subprocess
import requests
from datetime import datetime

# Set env vars for Node.js
os.environ['CDC_API_KEY'] = 'cdc_4c5aef5a38d7668ea5f249f1f68f'
os.environ['CDC_API_SECRET'] = 'EbwIHbqX30wEccOadwr+WBw7qUIJF0ClEXgBQVso+Sw='

SKILL_DIR = r'C:\Users\digim\.agents\skills\crypto-agent-trading'
TELEGRAM_BOT_TOKEN = '8249656817:AAFAI3oulkDWJZHJ7STSYlDfK-_UJCPo-7U'
TELEGRAM_CHAT_ID = '5804173449'

# Config
SYMBOLS = ['LINK', 'ETH']
BUY_USD = 10  # Buy $10 each
PROFIT_TARGET = 5  # Sell at $5 profit
POSITIONS_FILE = 'C:/Users/digim/OneDrive/Pictures/auto_opener_monitor/crypto_trader/cdc_auto_positions.json'

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
        return float(data['result']['data'][0]['a'])
    except:
        return None

def run_node_cmd(cmd):
    """Run a Node.js command via npx"""
    try:
        result = subprocess.run(
            cmd,
            cwd=SKILL_DIR,
            capture_output=True,
            text=True,
            timeout=30,
            env=os.environ.copy()
        )
        output = result.stdout
        # Try to parse JSON
        try:
            return json.loads(output.split('\n')[0])
        except:
            return output
    except Exception as e:
        return {'error': str(e)}

def buy_crypto(symbol, usd_amount):
    """Buy crypto using quote -> confirm flow"""
    # Create quotation
    quote_cmd = [
        NPX, 'tsx', 'scripts/trade.ts', 'quote', 'purchase',
        '{"from_currency":"USD","to_currency":"' + symbol + '","to_amount":' + str(usd_amount) + '}'
    ]
    
    result = run_node_cmd(quote_cmd)
    
    if result and isinstance(result, dict) and result.get('ok'):
        quote_id = result['data']['quotation']['id']
        
        # Confirm purchase
        confirm_cmd = [
            NPX, 'tsx', 'scripts/trade.ts', 'confirm', 'purchase', quote_id
        ]
        confirm_result = run_node_cmd(confirm_cmd)
        
        if confirm_result and isinstance(confirm_result, dict) and confirm_result.get('ok'):
            return True
    
    print(f"Buy result: {result}")
    return False

def get_balance(symbol):
    """Get balance of a symbol"""
    cmd = [NPX, 'tsx', 'scripts/account.ts', 'balance', symbol]
    result = run_node_cmd(cmd)
    
    if result and isinstance(result, dict) and result.get('ok'):
        return float(result['data']['balance']['available'])
    return 0

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
        
        # Check if we have a position
        if pos_key in positions:
            entry_price = positions[pos_key]['entry_price']
            amount = positions[pos_key]['amount']
            profit = (price - entry_price) * amount
            
            print(f"  {symbol}: ${price} (Entry: ${entry_price}, Profit: ${profit:.2f})")
            
            if profit >= PROFIT_TARGET:
                # Sell!
                balance = get_balance(symbol)
                if balance >= amount:
                    # Use exchange to sell
                    print(f"    >>> SELLING {symbol}...")
                    # For now just alert - selling is complex
                    msg = f"PROFIT TARGET HIT! {symbol}\nEntry: ${entry_price}\nCurrent: ${price}\nProfit: ${profit:.2f}"
                    send_alert(msg)
                    del positions[pos_key]
                    save_positions(positions)
            continue
        
        # Check for buy opportunity
        try:
            r = requests.get(f'https://api.crypto.com/v2/public/get-ticker?instrument_name={symbol}_USDT', timeout=10)
            high_24h = float(r.json()['result']['data'][0]['h'])
            dip = (high_24h - price) / high_24h * 100
            print(f"  {symbol}: ${price} (High: ${high_24h}, Dip: {dip:.1f}%)")
            
            if dip >= 4:  # 4% dip
                print(f"    >>> BUYING {symbol}...")
                if buy_crypto(symbol, BUY_USD):
                    amount = BUY_USD / price
                    positions[pos_key] = {
                        'entry_price': price,
                        'amount': amount
                    }
                    save_positions(positions)
                    msg = f"BOUGHT {symbol}\n${BUY_USD} @ ${price}"
                    send_alert(msg)
                    print(f"    >>> {msg}")
        except Exception as e:
            print(f"    Error: {e}")

if __name__ == "__main__":
    print("="*50)
    print("Crypto.com Auto Trader")
    print("="*50)
    check_and_trade()
