import ccxt
import os

bybit = ccxt.bybit({
    'apiKey': os.getenv('BYBIT_API_KEY'),
    'secret': os.getenv('BYBIT_API_SECRET'),
    'testnet': False
})

# DOGE SHORT: entry 0.1013, size 493
entry = 0.1013
# SHORT TP: below entry (lower), SL: above entry (higher)
tp_price = round(entry * 0.975, 6)  # 2.5% profit
sl_price = round(entry * 1.015, 6)  # 1.5% loss

print(f"DOGE SHORT - Entry: {entry}")
print(f"Setting TP: {tp_price} (2.5% below entry)")
print(f"Setting SL: {sl_price} (1.5% above entry)")

try:
    result = bybit.private_post_v5_position_set_trading_stop({
        'category': 'linear',
        'symbol': 'DOGEUSDT',
        'positionIdx': 1,
        'takeProfit': str(tp_price),
        'stopLoss': str(sl_price),
        'triggerDirection': 1  # 1 for SHORT
    })
    print("Result:", result)
except Exception as e:
    print(f"Error: {e}")
