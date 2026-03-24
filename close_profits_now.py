"""
Close profitable trendline positions
"""
import ccxt
import time

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

# Positions to close (from trendline logs)
positions_to_close = [
    {'symbol': 'SOL/USDT:USDT', 'side': 'long', 'contracts': 3.0, 'pnl': 3.40},
    {'symbol': 'XRP/USDT:USDT', 'side': 'long', 'contracts': 70.0, 'pnl': 0.89},
    {'symbol': 'ADA/USDT:USDT', 'side': 'long', 'contracts': 382.0, 'pnl': 0.71},
]

print("="*60)
print("CLOSING PROFITABLE POSITIONS")
print("="*60)
print()

total_profit = 0
closed_count = 0

for pos in positions_to_close:
    symbol = pos['symbol']
    side = pos['side']
    contracts = pos['contracts']
    pnl = pos['pnl']
    
    # Close position (opposite side)
    close_side = 'sell' if side == 'long' else 'buy'
    
    try:
        print(f"Closing {symbol} {side.upper()} {contracts} contracts...")
        order = exchange.create_market_order(symbol, close_side, contracts)
        print(f"  CLOSED: +${pnl:.2f} profit")
        total_profit += pnl
        closed_count += 1
        time.sleep(1)
    except Exception as e:
        print(f"  Error closing {symbol}: {e}")

print()
print("="*60)
print(f"SUMMARY: Closed {closed_count} positions")
print(f"Total profit locked in: ${total_profit:.2f}")
print("="*60)
print()
print("Remaining positions:")
print("  - DOGE/USDT (holding, -1.67%)")
print("  - NEAR/USDT (holding, -1.89%)")
print()
print("Ready for new entry signals!")
