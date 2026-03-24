from pybit import usdt_perpetual
import os

session = usdt_perpetual(testnet=False, api_key='bsK06QDhsagOWwFsXQ', api_secret='ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa')

# Cancel all DOGE orders
result = session.cancel_all_orders(category='linear', symbol='DOGEUSDT')
print(result)

# Also check for any open orders
orders = session.get_open_orders(category='linear', symbol='DOGEUSDT')
print("\nOpen orders after cancel:")
print(orders)
