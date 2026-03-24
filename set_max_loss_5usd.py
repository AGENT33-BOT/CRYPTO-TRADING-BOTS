"""
Set Maximum $5 Loss Protection for All Positions
Updates stop losses to ensure no position loses more than $5
"""
import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

MAX_LOSS_PER_POSITION = 5.0  # $5 max loss

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

exchange.set_sandbox_mode(False)

print("=" * 70)
print("SETTING $5 MAX LOSS PROTECTION FOR ALL POSITIONS")
print("=" * 70)

try:
    # Fetch positions
    positions = exchange.fetch_positions()
    
    for pos in positions:
        symbol = pos.get('symbol', '')
        contracts = float(pos.get('contracts', 0))
        
        if contracts == 0:
            continue
        
        side = pos.get('side', '').lower()
        entry_price = float(pos.get('entryPrice', 0))
        current_price = float(pos.get('markPrice', pos.get('lastPrice', entry_price)))
        
        print(f"\n[POSITION] {symbol}")
        print(f"   Side: {side.upper()}")
        print(f"   Size: {contracts}")
        print(f"   Entry: ${entry_price:.4f}")
        print(f"   Current: ${current_price:.4f}")
        
        # Calculate SL price for max $5 loss
        position_value = contracts * entry_price
        
        if side == 'long':
            # For LONG: SL = Entry - ($5 / contracts)
            sl_price = entry_price - (MAX_LOSS_PER_POSITION / contracts)
            # Ensure SL is below entry
            if sl_price >= entry_price:
                sl_price = entry_price * 0.985  # 1.5% default
        else:
            # For SHORT: SL = Entry + ($5 / contracts)
            sl_price = entry_price + (MAX_LOSS_PER_POSITION / contracts)
            # Ensure SL is above entry
            if sl_price <= entry_price:
                sl_price = entry_price * 1.015  # 1.5% default
        
        # Calculate actual loss if SL hits
        if side == 'long':
            actual_loss = contracts * (entry_price - sl_price)
        else:
            actual_loss = contracts * (sl_price - entry_price)
        
        print(f"   Position Value: ${position_value:.2f}")
        print(f"   New SL: ${sl_price:.4f}")
        print(f"   Max Loss: ${actual_loss:.2f}")
        
        if actual_loss <= MAX_LOSS_PER_POSITION:
            print(f"   [OK] Within $5 limit")
        else:
            print(f"   [ADJUSTING] to meet $5 limit...")
            # Recalculate
            if side == 'long':
                sl_price = entry_price - (MAX_LOSS_PER_POSITION / contracts)
            else:
                sl_price = entry_price + (MAX_LOSS_PER_POSITION / contracts)
            print(f"   Adjusted SL: ${sl_price:.4f}")
        
        # Cancel existing SL orders
        try:
            orders = exchange.fetch_open_orders(symbol)
            for order in orders:
                if order.get('type') == 'stop':
                    exchange.cancel_order(order['id'], symbol)
                    print(f"   [CANCELLED] old SL order")
        except:
            pass
        
        # Set new SL
        try:
            amount = contracts
            if side == 'long':
                # Close long with sell stop
                order = exchange.create_order(
                    symbol=symbol,
                    type='stop',
                    side='sell',
                    amount=amount,
                    price=None,
                    params={'stopPrice': sl_price, 'reduceOnly': True}
                )
            else:
                # Close short with buy stop
                order = exchange.create_order(
                    symbol=symbol,
                    type='stop',
                    side='buy',
                    amount=amount,
                    price=None,
                    params={'stopPrice': sl_price, 'reduceOnly': True}
                )
            print(f"   [OK] SL order placed: {order.get('id', 'N/A')}")
        except Exception as e:
            print(f"   [ERROR] setting SL: {e}")
    
    print("\n" + "=" * 70)
    print("$5 MAX LOSS PROTECTION APPLIED TO ALL POSITIONS")
    print("=" * 70)
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
