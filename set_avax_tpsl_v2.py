import ccxt
import time

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

symbol = 'AVAX/USDT:USDT'

# Get position
positions = exchange.fetch_positions([symbol])
if not positions or len(positions) == 0:
    print("No position found")
    exit()

pos = positions[0]
contracts = float(pos.get('contracts', 0))
if contracts == 0:
    print("No position found")
    exit()

side = pos['side']
entry = float(pos['entryPrice'])
size = contracts

print(f"Position: {side.upper()} {size} AVAX @ ${entry}")

# Calculate TP/SL (2% SL, 4% TP)
if side == 'long':
    stop_loss = round(entry * 0.98, 4)
    take_profit = round(entry * 1.04, 4)
    close_side = 'sell'
else:
    stop_loss = round(entry * 1.02, 4)
    take_profit = round(entry * 0.96, 4)
    close_side = 'buy'

print(f"Setting SL: ${stop_loss}")
print(f"Setting TP: ${take_profit}")

# Cancel existing orders first
try:
    exchange.cancel_all_orders(symbol)
    print("Cancelled existing orders")
    time.sleep(1)
except Exception as e:
    print(f"No orders to cancel or error: {e}")

# Set Take Profit as limit order
try:
    tp_order = exchange.create_order(
        symbol=symbol,
        type='limit',
        side=close_side,
        amount=size,
        price=take_profit,
        params={'reduceOnly': True}
    )
    print(f"[OK] Take Profit set: ${take_profit}")
except Exception as e:
    print(f"[ERROR] TP: {e}")

# Set Stop Loss using conditional order
try:
    sl_order = exchange.create_order(
        symbol=symbol,
        type='market',
        side=close_side,
        amount=size,
        price=None,
        params={
            'triggerPrice': stop_loss,
            'reduceOnly': True
        }
    )
    print(f"[OK] Stop Loss trigger set: ${stop_loss}")
except Exception as e:
    print(f"[ERROR] SL: {e}")

print("Done!")
