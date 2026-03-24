from pybit.unified_trading import HTTP
import os
from dotenv import load_dotenv

load_dotenv('.env.bybit')
sess = HTTP(api_key=os.getenv('BYBIT_API_KEY'), api_secret=os.getenv('BYBIT_API_SECRET'))

print("=== OPEN ORDERS ===")
r = sess.get_open_orders(category='linear', settleCoin='USDT')
print(f"Linear orders: {len(r['result']['list'])}")
for o in r['result']['list'][:10]:
    print(f"  {o.get('symbol')} | {o.get('side')} | {o.get('orderType')} | qty: {o.get('qty')}")

print("\n=== RECENT TRADES ===")
import time
now = int(time.time() * 1000)
two_hours_ago = now - (2 * 60 * 60 * 1000)

r = sess.get_executions(category='linear', settleCoin='USDT', startTime=two_hours_ago)
print(f"Executions: {len(r['result']['list'])}")
for e in r['result']['list'][:10]:
    print(f"  {e.get('symbol')} | {e.get('side')} | {e.get('orderType')} | qty: {e.get('execQty')} | price: {e.get('execPrice')}")
