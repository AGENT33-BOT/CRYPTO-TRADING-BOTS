"""
Close profitable positions to free up margin
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
print("POSITION MANAGER - Close Profitable Positions")
print("="*60)
print()

# Fetch positions
try:
    positions = exchange.fetch_positions()
    
    profitable_positions = []
    
    for pos in positions:
        contracts = float(pos.get('contracts', 0) or 0)
        if contracts != 0:
            symbol = pos['symbol']
            side = pos['side']
            pnl = float(pos.get('unrealizedPnl', 0) or 0)
            entry = float(pos.get('entryPrice', 0) or 0)
            mark = float(pos.get('markPrice', 0) or 0)
            
            print(f"{symbol}: {side.upper()} {contracts} contracts")
            print(f"  Entry: ${entry:.4f} | Mark: ${mark:.4f}")
            print(f"  PnL: ${pnl:.2f}")
            
            if pnl > 0:
                profitable_positions.append({
                    'symbol': symbol,
                    'side': side,
                    'contracts': contracts,
                    'pnl': pnl
                })
                print(f"  ✅ PROFITABLE - Will close")
            else:
                print(f"  🔴 Losing - Holding")
            print()
    
    if not profitable_positions:
        print("No profitable positions to close.")
    else:
        print(f"\nFound {len(profitable_positions)} profitable positions to close.")
        print("="*60)
        
        confirm = input("\nClose all profitable positions? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            for pos in profitable_positions:
                symbol = pos['symbol']
                side = pos['side']
                contracts = pos['contracts']
                
                # Close position (opposite side)
                close_side = 'sell' if side == 'long' else 'buy'
                
                try:
                    print(f"\nClosing {symbol} {side}...")
                    order = exchange.create_market_order(symbol, close_side, contracts)
                    print(f"✅ Closed {symbol}: ${pos['pnl']:.2f} profit")
                    time.sleep(1)
                except Exception as e:
                    print(f"❌ Failed to close {symbol}: {e}")
            
            print("\n" + "="*60)
            print("Done! Check your Bybit account for updated balance.")
        else:
            print("Cancelled. No positions were closed.")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
