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
    stop_loss = entry * 0.98
    take_profit = entry * 1.04
    close_side = 'sell'
else:
    stop_loss = entry * 1.02
    take_profit = entry * 0.96
    close_side = 'buy'

print(f"Setting SL: ${stop_loss:.4f}")
print(f"Setting TP: ${take_profit:.4f}")

# Cancel existing orders first
try:
    exchange.cancel_all_orders(symbol)
    print("Cancelled existing orders")
    time.sleep(1)
except Exception as e:
    print(f"No orders to cancel: {e}")

# Set Stop Loss
try:
    sl_order = exchange.create_order(
        symbol=symbol,
        type='stopLoss',
        side=close_side,
        amount=size,
        price=None,
        params={
            'stopLossPrice': round(stop_loss, 4),
            'reduceOnly': True
        }
    )
    print(f"✅ Stop Loss set: ${stop_loss:.4f}")
except Exception as e:
    print(f"❌ SL Error: {e}")

# Set Take Profit
try:
    tp_order = exchange.create_order(
        symbol=symbol,
        type='limit',
        side=close_side,
        amount=size,
        price=round(take_profit, 4),
        params={'reduceOnly': True}
    )
    print(f"✅ Take Profit set: ${take_profit:.4f}")
except Exception as e:
    print(f"❌ TP Error: {e}")

print("\nDone!")
