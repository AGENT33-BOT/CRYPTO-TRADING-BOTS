"""
Close all positions and open new $50 position
"""
import ccxt
import time

# API credentials
api_key = 'bsK06QDhsagOWwFsXQ'
api_secret = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

# Initialize exchange
exchange = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'swap',
        'adjustForTimeDifference': True,
    }
})
exchange.set_sandbox_mode(False)
exchange.load_markets()

print("=== CHECKING OPEN POSITIONS ===")

# Get all open positions
try:
    positions = exchange.fetch_positions()
    open_positions = [p for p in positions if float(p.get('contracts', 0)) != 0]
    
    if not open_positions:
        print("No open positions found.")
    else:
        print(f"Found {len(open_positions)} open position(s):")
        for pos in open_positions:
            symbol = pos['symbol']
            side = pos['side']
            size = pos['contracts']
            print(f"  {symbol}: {side} {size}")
            
            # Close position
            close_side = 'sell' if side == 'long' else 'buy'
            try:
                order = exchange.create_order(
                    symbol=symbol,
                    type='market',
                    side=close_side,
                    amount=abs(float(size)),
                    params={'reduceOnly': True}
                )
                print(f"  [OK] Closed {symbol} position")
            except Exception as e:
                print(f"  [ERR] Error closing {symbol}: {e}")
            
            time.sleep(0.5)
    
    print("\n=== OPENING NEW $50 POSITION ===")
    
    # Open a new DOGE/USDT position with $50
    symbol = 'DOGE/USDT:USDT'
    position_size = 50  # $50 USDT
    leverage = 3
    
    # Set leverage
    try:
        exchange.set_leverage(leverage, symbol)
        print(f"[OK] Set leverage to {leverage}x for {symbol}")
    except Exception as e:
        print(f"Leverage may already be set: {e}")
    
    # Get current price
    ticker = exchange.fetch_ticker(symbol)
    current_price = ticker['last']
    print(f"Current {symbol} price: ${current_price}")
    
    # Calculate amount
    amount = (position_size * leverage) / current_price
    
    # Get precision
    market = exchange.market(symbol)
    precision = market.get('precision', {}).get('amount', 0)
    min_amount = market.get('limits', {}).get('amount', {}).get('min', 0.1)
    
    # Adjust amount
    amount = round(amount, int(precision))
    amount = max(amount, float(min_amount))
    
    print(f"Opening LONG position: {amount} DOGE (${position_size} at {leverage}x leverage)")
    
    # Open position
    order = exchange.create_order(
        symbol=symbol,
        type='market',
        side='buy',
        amount=amount
    )
    
    print(f"[OK] Position opened! Order ID: {order['id']}")
    
    # Set TP/SL
    tp_price = round(current_price * 1.03, 4)  # 3% TP
    sl_price = round(current_price * 0.985, 4)  # 1.5% SL
    
    print(f"Setting TP: ${tp_price} (+3%)")
    print(f"Setting SL: ${sl_price} (-1.5%)")
    
    # Set stop loss
    try:
        sl_order = exchange.create_order(
            symbol=symbol,
            type='stop',
            side='sell',
            amount=amount,
            price=None,
            params={
                'stopPrice': sl_price,
                'triggerDirection': 2,  # Price falls to trigger
                'reduceOnly': True
            }
        )
        print(f"[OK] Stop loss set")
    except Exception as e:
        print(f"[WARN] Stop loss error: {e}")
    
    # Set take profit
    try:
        tp_order = exchange.create_order(
            symbol=symbol,
            type='limit',
            side='sell',
            amount=amount,
            price=tp_price,
            params={
                'reduceOnly': True
            }
        )
        print(f"[OK] Take profit set")
    except Exception as e:
        print(f"[WARN] Take profit error: {e}")
    
    print("\n=== POSITION SUMMARY ===")
    print(f"Symbol: {symbol}")
    print(f"Side: LONG")
    print(f"Size: ${position_size} USDT")
    print(f"Leverage: {leverage}x")
    print(f"Entry: ~${current_price}")
    print(f"Take Profit: ${tp_price} (+3%)")
    print(f"Stop Loss: ${sl_price} (-1.5%)")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n[OK] Done!")
