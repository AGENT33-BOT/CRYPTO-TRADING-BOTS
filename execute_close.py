import ccxt
import json
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
    
    # Get NEAR position
    print("Getting NEAR position...")
    positions = exchange.fetch_positions(['NEAR/USDT:USDT'])
    
    if positions and positions[0]['contracts'] > 0:
        pos = positions[0]
        print(f"Found NEAR position:")
        print(f"  Size: {pos['contracts']}")
        print(f"  Entry: ${float(pos['entryPrice']):.4f}")
        print(f"  Mark: ${float(pos['markPrice']):.4f}")
        print(f"  PnL: ${float(pos['unrealizedPnl']):.2f}")
        
        # Close 50%
        close_size = float(pos['contracts']) * 0.5
        print(f"\nClosing 50% = {close_size} contracts...")
        
        order = exchange.create_market_order(
            symbol='NEAR/USDT:USDT',
            side='sell',
            amount=close_size,
            params={'reduceOnly': True}
        )
        
        print(f"\nSUCCESS!")
        print(f"Order ID: {order['id']}")
        print(f"Closed: {close_size} NEAR")
        print(f"Side: {order['side']}")
        
        # Save log
        with open('trade_execution_log.json', 'a') as f:
            f.write(json.dumps({
                'time': datetime.now().isoformat(),
                'symbol': 'NEAR/USDT:USDT',
                'action': 'close_50_percent',
                'amount': close_size,
                'order_id': order['id'],
                'status': 'success'
            }) + '\n')
        
        print("\nProfit secured! 50% of NEAR position closed.")
        
    else:
        print("No NEAR position found or position is 0")
        
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
