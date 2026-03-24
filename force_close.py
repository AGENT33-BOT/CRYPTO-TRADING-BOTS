import ccxt

exchange = ccxt.bybit({
    'apiKey': 'bsK06QDhsagOWwFsXQ',
    'secret': 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa',
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})
exchange.set_sandbox_mode(False)

# Close NEAR position
print("Closing NEAR SHORT...")
try:
    exchange.create_market_buy_order('NEAR/USDT:USDT', 1.0)
    print("  NEAR closed!")
except Exception as e:
    print(f"  Error: {e}")

# Close DOGE position
print("Closing DOGE SHORT...")
try:
    exchange.create_market_buy_order('DOGE/USDT:USDT', 1.0)
    print("  DOGE closed!")
except Exception as e:
    print(f"  Error: {e}")

print("\nChecking positions again...")
positions = exchange.fetch_positions()
for pos in positions:
    if abs(float(pos['contracts'])) > 0:
        print(f"Still open: {pos['symbol']} - {pos['contracts']} contracts")

print("Done!")
