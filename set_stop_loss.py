import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

try:
    print("Setting STOP LOSS for BTC SHORT position...")
    exchange = ccxt.bybit({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'linear'}
    })
    
    exchange.load_markets()
    
    # Get position
    positions = exchange.fetch_positions(['BTC/USDT:USDT'])
    
    if positions and len(positions) > 0:
        pos = positions[0]
        size = float(pos['contracts'])
        entry = float(pos['entryPrice'])
        
        # Stop loss for SHORT: 2% above entry
        sl_price = entry * 1.02
        
        print(f"\nPosition: BTC SHORT {size} @ ${entry:.2f}")
        print(f"Setting Stop Loss at: ${sl_price:.2f}")
        print(f"(2% above entry = max loss ~$3.50)")
        
        # Create stop loss order
        # For Bybit, we use stopLossPrice parameter
        order = exchange.create_order(
            symbol='BTC/USDT:USDT',
            type='market',
            side='buy',
            amount=size,
            params={
                'stopLossPrice': sl_price,
                'reduceOnly': True
            }
        )
        
        print(f"\n✅ STOP LOSS SET!")
        print(f"Order ID: {order['id']}")
        print(f"Stop Price: ${sl_price:.2f}")
        
    else:
        print("No BTC position found.")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
