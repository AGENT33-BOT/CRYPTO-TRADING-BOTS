import ccxt
import os
import sys
import io
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

load_dotenv('.env.bybit')

exchange = ccxt.bybit({
    'apiKey': os.getenv('BYBIT_API_KEY'),
    'secret': os.getenv('BYBIT_API_SECRET'),
    'enableRateLimit': True,
})

print("Checking ETH position...")

# Get open positions
positions = exchange.fetch_positions(['ETH/USDT:USDT'])
for p in positions:
    print(f"Symbol: {p['symbol']}")
    print(f"Side: {p['side']}")
    print(f"Contracts: {p['contracts']}")
    print(f"Entry Price: {p['entryPrice']}")
    print(f"Unrealized PnL: {p['unrealizedPnl']}")
    
    if p['contracts'] and p['contracts'] > 0 and p['side'] == 'short':
        print(f"\nClosing SHORT {p['symbol']}...")
        try:
            order = exchange.create_market_buy_order(
                symbol=p['symbol'],
                amount=p['contracts'],
                params={'reduceOnly': True}
            )
            print(f"Order created: {order['id']}")
            print(f"Status: {order['status']}")
            print("ETH SHORT closed successfully")
        except Exception as e:
            print(f"Error: {e}")
