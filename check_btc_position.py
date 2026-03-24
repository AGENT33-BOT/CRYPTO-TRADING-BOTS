import ccxt
from datetime import datetime

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

try:
    print("Checking BTC position status...")
    exchange = ccxt.bybit({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'linear'}
    })
    
    exchange.load_markets()
    
    # Check BTC position specifically
    positions = exchange.fetch_positions(['BTC/USDT:USDT'])
    
    if positions and len(positions) > 0:
        pos = positions[0]
        size = float(pos.get('contracts', 0))
        
        if size > 0:
            print(f"\nBTC POSITION ACTIVE:")
            print(f"  Side: {pos['side'].upper()}")
            print(f"  Size: {size} BTC")
            print(f"  Entry: ${float(pos['entryPrice']):.2f}")
            print(f"  Mark: ${float(pos['markPrice']):.2f}")
            print(f"  PnL: ${float(pos['unrealizedPnl']):.2f}")
            print(f"\nPosition is OPEN and being monitored.")
        else:
            print("\nNo BTC position found - may have been closed.")
    else:
        print("\nNo positions found.")
        
except Exception as e:
    print(f"Error: {e}")
