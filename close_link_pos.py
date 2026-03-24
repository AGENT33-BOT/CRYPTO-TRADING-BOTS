import ccxt

API_KEY = "bsK06QDhsagOWwFsXQ"
API_SECRET = "ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa"

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

# Close LINK SHORT by buying (LONG direction)
symbol = 'LINK/USDT:USDT'
try:
    # Get position info first
    positions = exchange.fetch_positions([symbol])
    for pos in positions:
        if pos['symbol'] == symbol and float(pos['contracts']) != 0:
            size = abs(float(pos['contracts']))
            side = 'buy' if pos['side'] == 'short' else 'sell'
            print(f"Closing {pos['side']} position: {size} {symbol}")
            result = exchange.create_market_buy_order(symbol, size) if side == 'buy' else exchange.create_market_sell_order(symbol, size)
            print(f"Order result: {result}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
