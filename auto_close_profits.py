"""
Auto-close profitable positions (>1% gain)
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

print("="*60)
print("AUTO-CLOSING PROFITABLE POSITIONS (>1% gain)")
print("="*60)
print()

try:
    positions = exchange.fetch_positions()
    
    closed_count = 0
    total_profit = 0
    
    for pos in positions:
        contracts = float(pos.get('contracts', 0) or 0)
        if contracts != 0:
            symbol = pos['symbol']
            side = pos['side']
            pnl = float(pos.get('unrealizedPnl', 0) or 0)
            entry = float(pos.get('entryPrice', 0) or 0)
            mark = float(pos.get('markPrice', 0) or 0)
            
            # Calculate percentage
            if entry > 0:
                if side == 'long':
                    pct = ((mark - entry) / entry) * 100
                else:
                    pct = ((entry - mark) / entry) * 100
            else:
                pct = 0
            
            print(f"{symbol}: {side.upper()} {contracts} | PnL: ${pnl:.2f} ({pct:+.2f}%)")
            
            # Close if profitable (>1%)
            if pct > 1.0:
                close_side = 'sell' if side == 'long' else 'buy'
                try:
                    order = exchange.create_market_order(symbol, close_side, contracts)
                    print(f"  CLOSED: +${pnl:.2f} profit")
                    closed_count += 1
                    total_profit += pnl
                    time.sleep(1)
                except Exception as e:
                    print(f"  Failed to close: {e}")
            else:
                print(f"  Holding (below 1% threshold)")
    
    print("\n" + "="*60)
    print(f"SUMMARY:")
    print(f"  Positions closed: {closed_count}")
    print(f"  Total profit: ${total_profit:.2f}")
    print("="*60)

except Exception as e:
    print(f"Error: {e}")
