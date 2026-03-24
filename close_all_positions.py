"""
Close all open positions on Bybit
"""
import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

exchange.load_markets()

print("Closing all positions...")
print("=" * 50)

pairs = ['SOL/USDT:USDT', 'XRP/USDT:USDT', 'ADA/USDT:USDT', 'DOGE/USDT:USDT', 'NEAR/USDT:USDT']

for symbol in pairs:
    try:
        # Close any position by creating market order in opposite direction
        positions = exchange.fetch_positions([symbol])
        for pos in positions:
            contracts = float(pos.get('contracts', 0))
            if contracts != 0:
                side = pos['side']
                print(f"Closing {symbol}: {side} {contracts}")
                if side == 'long':
                    exchange.create_market_sell_order(symbol, contracts)
                else:
                    exchange.create_market_buy_order(symbol, contracts)
                print(f"  -> Closed")
    except Exception as e:
        print(f"{symbol}: {e}")

print("=" * 50)
print("Done")
