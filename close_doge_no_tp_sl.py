import ccxt

api_key = 'bsK06QDhsagOWwFsXQ'
api_secret = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'swap',
        'adjustForTimeDifference': True,
    }
})

exchange.set_sandbox_mode(False)
exchange.load_markets()

symbol = 'DOGE/USDT:USDT'

positions = exchange.fetch_positions([symbol])
for p in positions:
    size = float(p.get('contracts', p.get('size', 0)) or 0)
    side = p.get('side')
    if size == 0 or side != 'long':
        continue
    market = exchange.market(symbol)
    print(f"Closing DOGE position: {size} contracts LONG -> market SELL")
    order = exchange.create_order(symbol, 'market', 'sell', size)
    print("Order response:", order)
    break
else:
    print("No DOGE long position found or already flat.")
