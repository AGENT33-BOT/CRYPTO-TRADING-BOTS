from pybit.unified_trading import HTTP
import os
from dotenv import load_dotenv

load_dotenv('.env.bybit')
sess = HTTP(api_key=os.getenv('BYBIT_API_KEY'), api_secret=os.getenv('BYBIT_API_SECRET'))

print("=== ALL POSITIONS (Linear) ===")
r = sess.get_positions(category='linear', settleCoin='USDT')
for p in r['result']['list']:
    size = float(p.get('size', 0))
    if size > 0:
        print(f"{p.get('symbol')} | {p.get('side')} | size: {size} | entry: {p.get('avgPrice')} | PnL: {p.get('unrealisedPnl')}")

print("\n=== ALL POSITIONS (Spot) ===")
try:
    r = sess.get_positions(category='spot', settleCoin='USDT')
    for p in r['result']['list']:
        size = float(p.get('size', 0))
        if size > 0:
            print(f"{p.get('symbol')} | {p.get('side')} | size: {size}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== UNREALIZED PNL ===")
r = sess.get_positions(category='linear', settleCoin='USDT')
total_pnl = 0
for p in r['result']['list']:
    size = float(p.get('size', 0))
    if size > 0:
        pnl = float(p.get('unrealisedPnl', 0))
        total_pnl += pnl
        print(f"{p.get('symbol')}: {pnl:.2f}")
print(f"Total: {total_pnl:.2f}")
