import ccxt
from datetime import datetime

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

try:
    print("Connecting to Bybit...")
    exchange = ccxt.bybit({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'linear'}
    })
    
    exchange.load_markets()
    
    # Close NEAR SHORT position
    print("\nChecking NEAR position...")
    positions = exchange.fetch_positions(['NEAR/USDT:USDT'])
    
    if positions and positions[0]['contracts'] > 0:
        pos = positions[0]
        size = float(pos['contracts'])
        side = pos['side']
        
        print(f"Found NEAR {side.upper()} position: {size} contracts")
        print(f"Entry: ${float(pos['entryPrice']):.4f}")
        print(f"Mark: ${float(pos['markPrice']):.4f}")
        print(f"PnL: ${float(pos['unrealizedPnl']):.2f}")
        
        # For SHORT, we BUY to close
        print(f"\nClosing NEAR SHORT position...")
        order = exchange.create_market_order(
            symbol='NEAR/USDT:USDT',
            side='buy',  # Buy to close SHORT
            amount=size,
            params={'reduceOnly': True}
        )
        
        print(f"\n✅ SUCCESS!")
        print(f"Order ID: {order['id']}")
        print(f"Closed: {size} NEAR SHORT")
        print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
        
    else:
        print("No NEAR position found")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
