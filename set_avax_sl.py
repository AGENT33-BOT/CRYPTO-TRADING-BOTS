import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

symbol = 'AVAX/USDT:USDT'

# For SHORT position, SL is above entry (price going up)
# triggerDirection: 'ascending' means trigger when price goes up
stop_loss = 9.0025
size = 20.0

print(f"Setting SL for SHORT at ${stop_loss}")

try:
    sl_order = exchange.create_order(
        symbol=symbol,
        type='market',
        side='buy',  # Buy to close SHORT
        amount=size,
        price=None,
        params={
            'triggerPrice': stop_loss,
            'triggerDirection': 'ascending',  # Price going up triggers SL
            'reduceOnly': True
        }
    )
    print(f"[OK] Stop Loss set: ${stop_loss}")
except Exception as e:
    print(f"[ERROR] {e}")
