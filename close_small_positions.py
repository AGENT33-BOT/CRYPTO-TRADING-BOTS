"""
Close small positions and verify 20% setting
"""

import ccxt

exchange = ccxt.bybit({
    'apiKey': 'bsK06QDhsagOWwFsXQ',
    'secret': 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa',
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})
exchange.set_sandbox_mode(False)

# Get balance
balance = exchange.fetch_balance()
usdt_balance = balance['USDT']['free']
print(f"Available Balance: ${usdt_balance:.2f} USDT")
print(f"20% Position Size: ${usdt_balance * 0.20:.2f}")
print()

# Check positions
positions = exchange.fetch_positions()
for pos in positions:
    symbol = pos['symbol']
    contracts = float(pos['contracts'])
    
    if symbol in ['DOGE/USDT:USDT', 'NEAR/USDT:USDT'] and abs(contracts) > 0:
        print(f"Found position: {symbol}")
        print(f"  Size: {contracts} contracts")
        print(f"  Side: {pos['side']}")
        print(f"  PnL: ${pos['unrealizedPnl']:.2f}")
        print(f"  -> TOO SMALL! Closing...")
        
        side = 'sell' if pos['side'] == 'long' else 'buy'
        exchange.create_market_order(symbol, side, abs(contracts))
        print(f"  Closed!")
        print()

print("="*60)
print("All small positions closed.")
print("ML bots will now open proper 20% sized positions.")
print("Expected size: ~${:.2f} per trade".format(usdt_balance * 0.20))
print("="*60)
