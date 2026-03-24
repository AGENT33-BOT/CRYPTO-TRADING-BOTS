from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
import os
from dotenv import load_dotenv
load_dotenv('.alpaca_env')

client = TradingClient(os.getenv('APCA_API_KEY_ID'), os.getenv('APCA_API_SECRET_KEY'), paper=True)
orders = client.get_orders(GetOrdersRequest(status='open'))
print('OPEN ORDERS (TP/SL):')
if orders:
    for o in orders:
        print(f'  {o.symbol} | {o.side} | {o.type} | Qty: {o.qty} | Limit: {o.limit_price} | Stop: {o.stop_price}')
else:
    print('  None - No open TP/SL orders')
