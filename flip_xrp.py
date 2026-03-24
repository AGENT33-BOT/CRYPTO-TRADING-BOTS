from bybit_trader import BybitTrader
import os

api_key = os.getenv('BYBIT_API_KEY', 'JzFYPveGBhDGRDNNWL')
api_secret = os.getenv('BYBIT_API_SECRET', 'hJxF2qGJkGhmnNNRTT')

trader = BybitTrader(api_key, api_secret)

# Close XRP SHORT position
print('Closing XRP SHORT position...')
result = trader.close_position('XRP/USDT:USDT')
print(result)

print('\nNow opening XRP LONG position...')
# Re-open as LONG
trader.open_position('XRP/USDT:USDT', 'long', 10)
print('Done!')
