import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

try:
    print("Setting TP/SL for existing BTC position...")
    exchange = ccxt.bybit({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'linear'}
    })
    
    exchange.load_markets()
    
    # Get current position
    positions = exchange.fetch_positions(['BTC/USDT:USDT'])
    if not positions or len(positions) == 0:
        print("No position found")
        exit()
    
    pos = positions[0]
    entry = float(pos['entryPrice'])
    size = float(pos['contracts'])
    
    print(f"Position: BTC SHORT {size} @ ${entry:.2f}")
    
    # Calculate TP/SL prices
    tp_price = round(entry * 0.96, 2)  # 4% below for SHORT
    sl_price = round(entry * 1.02, 2)  # 2% above for SHORT
    
    print(f"\nSetting:")
    print(f"  Take Profit: ${tp_price}")
    print(f"  Stop Loss: ${sl_price}")
    
    # Use Bybit's private API to set TP/SL on position
    # This uses the trading-stop endpoint
    response = exchange.private_post_v5_position_trading_stop({
        'category': 'linear',
        'symbol': 'BTCUSDT',
        'takeProfit': str(tp_price),
        'stopLoss': str(sl_price),
        'tpTriggerBy': 'MarkPrice',
        'slTriggerBy': 'MarkPrice',
        'tpslMode': 'Full',
        'tpSize': str(size),
        'slSize': str(size)
    })
    
    print(f"\nResponse: {response}")
    
    if response.get('retCode') == 0:
        print("\n✅ TP/SL SET SUCCESSFULLY!")
        print(f"  TP: ${tp_price}")
        print(f"  SL: ${sl_price}")
    else:
        print(f"\n❌ Error: {response.get('retMsg', 'Unknown error')}")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
