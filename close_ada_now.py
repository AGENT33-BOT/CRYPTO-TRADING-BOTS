import ccxt
import sys

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

exchange.set_sandbox_mode(False)

# Close ADA position
symbol = 'ADA/USDT:USDT'
print(f"Closing {symbol} position...")

try:
    # Get position
    positions = exchange.fetch_positions([symbol])
    for pos in positions:
        if pos['symbol'] == symbol and float(pos['contracts']) != 0:
            side = pos['side']
            size = abs(float(pos['contracts']))
            
            # Close by opening opposite position
            if side == 'short':
                order = exchange.create_market_buy_order(symbol, size)
            else:
                order = exchange.create_market_sell_order(symbol, size)
            
            print(f"[OK] Closed {size} {symbol} {side}")
            print(f"Order ID: {order['id']}")
            sys.exit(0)
    
    print("[INFO] No position found")
    
except Exception as e:
    print(f"[ERROR] {e}")
