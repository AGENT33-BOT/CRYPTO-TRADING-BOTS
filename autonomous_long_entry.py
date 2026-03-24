from pybit.unified_trading import HTTP

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

session = HTTP(testnet=False, api_key=API_KEY, api_secret=API_SECRET)

print("AGENT33 AUTONOMOUS LONG ENTRY")
print("=" * 50)

# Get current SOL price
ticker = session.get_tickers(category='linear', symbol='SOLUSDT')
price = float(ticker['result']['list'][0]['lastPrice'])

print(f"SOL Price: ${price}")
print(f"Strategy: LONG - Riding the pump")
print(f"Position Size: $30 USDT")

# Calculate size (SOL uses 0.01 precision)
qty = round(30 / price, 1)
print(f"Quantity: {qty} SOL")

# Set leverage first (skip if already set)
# print("\nSetting 3x leverage...")
# session.set_leverage(
#     category='linear',
#     symbol='SOLUSDT',
#     buyLeverage='3',
#     sellLeverage='3'
# )

# Open LONG position
print("Opening LONG position...")
order = session.place_order(
    category='linear',
    symbol='SOLUSDT',
    side='Buy',
    orderType='Market',
    qty=str(qty),
    leverage='3'
)

print(f"Order ID: {order['result']['orderId']}")

# Set TP/SL immediately
tp_price = round(price * 1.095, 2)  # +9.5%
sl_price = round(price * 0.945, 2)  # -5.5%

print(f"\nSetting TP @ ${tp_price} (+9.5%)")
print(f"Setting SL @ ${sl_price} (-5.5%)")

session.set_trading_stop(
    category='linear',
    symbol='SOLUSDT',
    positionIdx=0,
    takeProfit=str(tp_price),
    stopLoss=str(sl_price),
    tpTriggerBy='LastPrice',
    slTriggerBy='LastPrice',
    tpslMode='Full'
)

print("\n[OK] Position opened with TP/SL protection")
print(f"Target: ${tp_price} | Stop: ${sl_price}")
