import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

try:
    print("Checking BTC position TP/SL status...")
    exchange = ccxt.bybit({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'linear'}
    })
    
    exchange.load_markets()
    
    # Get position details
    positions = exchange.fetch_positions(['BTC/USDT:USDT'])
    
    if positions and len(positions) > 0:
        pos = positions[0]
        
        print(f"\nPosition Details:")
        print(f"  Symbol: {pos['symbol']}")
        print(f"  Side: {pos['side']}")
        print(f"  Size: {pos['contracts']}")
        print(f"  Entry: ${float(pos['entryPrice']):.2f}")
        print(f"  Mark: ${float(pos['markPrice']):.2f}")
        print(f"  Liquidation: ${float(pos.get('liquidationPrice', 0)):.2f}")
        
        # Check for TP/SL orders
        print(f"\nChecking for TP/SL orders...")
        
        try:
            # Get open orders
            orders = exchange.fetch_open_orders('BTC/USDT:USDT')
            
            if orders:
                print(f"\nOpen Orders ({len(orders)}):")
                for order in orders:
                    print(f"  - {order['type']} {order['side']} @ ${float(order['price']):.2f} (Amount: {order['amount']})")
            else:
                print("\n⚠️  NO TP/SL ORDERS FOUND!")
                print("Position is UNPROTECTED!")
                
                # Set TP/SL now
                print("\nSetting TP/SL now...")
                
                entry = float(pos['entryPrice'])
                size = float(pos['contracts'])
                side = pos['side']
                
                # For SHORT position
                tp_price = entry * 0.96  # 4% below entry
                sl_price = entry * 1.02  # 2% above entry
                
                print(f"  Take Profit: ${tp_price:.2f}")
                print(f"  Stop Loss: ${sl_price:.2f}")
                
                # Set stop loss
                sl_order = exchange.create_order(
                    symbol='BTC/USDT:USDT',
                    type='market',
                    side='buy',  # Buy to close SHORT
                    amount=size,
                    params={
                        'stopLossPrice': sl_price,
                        'reduceOnly': True
                    }
                )
                print(f"  Stop Loss set: {sl_order['id']}")
                
                # Set take profit
                tp_order = exchange.create_order(
                    symbol='BTC/USDT:USDT',
                    type='limit',
                    side='buy',
                    amount=size,
                    price=tp_price,
                    params={'reduceOnly': True}
                )
                print(f"  Take Profit set: {tp_order['id']}")
                
                print("\n✅ TP/SL PROTECTION ACTIVE!")
                
        except Exception as e:
            print(f"Error checking/setting orders: {e}")
            
    else:
        print("No BTC position found.")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
