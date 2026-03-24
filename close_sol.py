import ccxt

# Bybit credentials from working bots
apiKey = 'bsK06QDhsagOWwFsXQ'
api_secret = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': apiKey,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

# Close SOL SHORT (was Sell 0.3) - need to Buy to close
try:
    # Close by placing opposite order
    order = exchange.create_order(
        symbol='SOL/USDT:USDT',
        type='market',
        side='buy',
        amount=0.3
    )
    print("SOL SHORT closed!")
    print("Order:", order.get('status'), order.get('id'))
except Exception as e:
    print("Error:", e)
