from pybit import usdt_perpetual
import os
from dotenv import load_dotenv
load_dotenv('.env.bybit')

session = usdt_perpetual.HTTP(
    endpoint='https://api.bybit.com',
    api_key=os.getenv('BYBIT_API_KEY'),
    api_secret=os.getenv('BYBIT_API_SECRET')
)

# Get open orders
orders = session.get_open_orders(category='linear')['result']['list']
print(f'Open orders: {len(orders)}')

for o in orders:
    print(f"  {o['symbol']} | {o['side']} | {o['orderType']} | Qty: {o['qty']} | Price: {o.get('price', 'market')}")

# Cancel all
if orders:
    for o in orders:
        result = session.cancel_order(category='linear', symbol=o['symbol'], orderId=o['orderId'])
        print(f"Cancelled {o['symbol']}")
    print(f"\nTotal cancelled: {len(orders)}")
else:
    print('No orders to cancel')
