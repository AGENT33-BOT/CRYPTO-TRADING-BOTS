import os
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv
from pybit.unified_trading import HTTP

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / '.env.bybit'

load_dotenv(ENV_PATH)
API_KEY = os.getenv('BYBIT_API_KEY')
API_SECRET = os.getenv('BYBIT_API_SECRET')

session = HTTP(api_key=API_KEY, api_secret=API_SECRET, testnet=False)

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

print("="*60)
print("BYBIT FUTURES - CLOSED PNL BY SYMBOL (LAST 30 DAYS)")
print("="*60)

# Get closed PnL
try:
    result = session.get_closed_pnl(category='linear', limit=100)
    if result.get('retCode') == 0:
        trades = result.get('result', {}).get('list', [])
        
        symbol_pnl = defaultdict(lambda: {'wins': 0, 'losses': 0, 'profit': 0.0, 'trades': 0})
        
        for t in trades:
            symbol = t.get('symbol')
            pnl = safe_float(t.get('closedPnl'))
            order_id = t.get('orderId')
            
            symbol_pnl[symbol]['trades'] += 1
            symbol_pnl[symbol]['profit'] += pnl
            if pnl > 0:
                symbol_pnl[symbol]['wins'] += 1
            else:
                symbol_pnl[symbol]['losses'] += 1
        
        print(f"\n{'SYMBOL':<20} {'TRADES':<8} {'WINS':<6} {'LOSSES':<8} {'NET PNL':<12}")
        print("-"*60)
        
        sorted_symbols = sorted(symbol_pnl.items(), key=lambda x: x[1]['profit'])
        
        total_profit = 0
        for symbol, data in sorted_symbols:
            print(f"{symbol:<20} {data['trades']:<8} {data['wins']:<6} {data['losses']:<8} ${data['profit']:+,.2f}")
            total_profit += data['profit']
        
        print("-"*60)
        print(f"{'TOTAL':<20} {sum(d['trades'] for _,d in sorted_symbols):<8}")
        print(f"\nTOTAL NET PNL: ${total_profit:+,.2f}")
    else:
        print(f"Error: {result.get('retMsg')}")
except Exception as e:
    print(f"Error: {e}")

# Also check wallet balance
print("\n" + "="*60)
print("CURRENT WALLET STATUS")
print("="*60)
try:
    wallet = session.get_wallet_balance(accountType='UNIFIED', coin='USDT')
    if wallet.get('retCode') == 0:
        bal = wallet['result']['list'][0]['coin'][0]
        print(f"Equity: ${safe_float(bal.get('equity')):.2f} USDT")
        print(f"Available: ${safe_float(bal.get('availableToWithdraw')):.2f} USDT")
        print(f"Locked: ${safe_float(bal.get('locked')):.2f} USDT")
except Exception as e:
    print(f"Error: {e}")
