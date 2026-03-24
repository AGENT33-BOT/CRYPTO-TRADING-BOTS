import os
import sys
from dotenv import load_dotenv
from pybit.unified_trading import HTTP

load_dotenv('.env.bybit')
s = HTTP(api_key=os.getenv('BYBIT_API_KEY'), api_secret=os.getenv('BYBIT_API_SECRET'))

symbol = "SOLUSDT"
leverage = 5

# Get current price
r = s.get_tickers(category='linear', symbol=symbol)
price = float(r['result']['list'][0]['lastPrice'])

# Round qty to 0.1 (step size)
qty = 16.4

print(f"Opening LONG {qty} SOLUSDT @ ${price} (leverage: {leverage}x)")

# Calculate TP/SL
tp_price = round(price * 1.03, 2)
sl_price = round(price * 0.975, 2)

print(f"TP: ${tp_price}, SL: ${sl_price}")

# Place order
result = s.place_order(
    category="linear",
    symbol=symbol,
    side="Buy",
    order_type="Market",
    qty=str(qty),
    take_profit=str(tp_price),
    stop_loss=str(sl_price)
)

print(f"Order: {result.get('retMsg', result)}")
