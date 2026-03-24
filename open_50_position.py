import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

symbol = 'SOL/USDT:USDT'
trade_amount = 50

# Get current price
ticker = exchange.fetch_ticker(symbol)
current_price = ticker['last']
print(f'SOL current price: ${current_price}')

# Calculate position size
leverage = 3
position_value = trade_amount * leverage
qty = round(position_value / current_price, 2)
print(f'Opening LONG {qty} SOL (~${position_value} with {leverage}x leverage)')

# Set leverage
try:
    exchange.set_leverage(leverage, symbol)
except:
    pass

# Open position
order = exchange.create_market_buy_order(symbol, qty)
print(f'Order placed: {order["id"]}')
print(f'Status: {order["status"]}')
avg_price = order["average"] if order["average"] else current_price
print(f'Filled: {order["filled"]} SOL @ ~${avg_price}')
