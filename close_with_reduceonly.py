import ccxt
import time

exchange = ccxt.bybit({
    'apiKey': 'bsK06QDhsagOWwFsXQ',
    'secret': 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa',
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})
exchange.set_sandbox_mode(False)

print("Attempting to close positions...")
print("="*50)

# Method 1: Try to close with reduceOnly
for symbol in ['NEAR/USDT:USDT', 'DOGE/USDT:USDT']:
    try:
        positions = exchange.fetch_positions([symbol])
        for pos in positions:
            contracts = float(pos['contracts'])
            if abs(contracts) > 0:
                print(f"\n{symbol}: {contracts} {pos['side']}")
                
                # Determine close side
                if pos['side'] == 'short':
                    close_side = 'buy'
                else:
                    close_side = 'sell'
                
                print(f"  Closing with {close_side} order...")
                
                # Try with reduceOnly parameter
                order = exchange.create_market_order(
                    symbol, 
                    close_side, 
                    abs(contracts),
                    {'reduceOnly': True}
                )
                print(f"  Success! Order ID: {order['id']}")
                time.sleep(2)
                
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "="*50)
print("Waiting 5 seconds for orders to process...")
time.sleep(5)

print("\nChecking positions again...")
positions = exchange.fetch_positions()
open_found = False
for pos in positions:
    contracts = float(pos['contracts'])
    if abs(contracts) > 0:
        open_found = True
        print(f"  STILL OPEN: {pos['symbol']} - {contracts} {pos['side']}")

if not open_found:
    print("  All positions closed successfully!")
