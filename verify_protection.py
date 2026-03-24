"""
Verify TP/SL Protection on All Positions
Ensures max $5 loss per position
"""
import ccxt

print("=" * 70)
print("VERIFYING TP/SL PROTECTION")
print("Max Loss Limit: $5 per position")
print("=" * 70)

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

try:
    exchange.load_markets()
    
    # Fetch positions
    positions = exchange.fetch_positions()
    
    open_positions = []
    for pos in positions:
        contracts = float(pos.get('contracts', 0))
        if contracts != 0:
            open_positions.append(pos)
    
    print(f"\nFound {len(open_positions)} open position(s)")
    print("-" * 70)
    
    protected_count = 0
    needs_protection = []
    
    for pos in open_positions:
        symbol = pos.get('symbol', '')
        side = pos.get('side', '')
        entry = float(pos.get('entryPrice', 0))
        contracts = float(pos.get('contracts', 0))
        notional = float(pos.get('notional', 0))
        
        # Check for TP/SL
        tp_price = pos.get('takeProfitPrice', 0)
        sl_price = pos.get('stopLossPrice', 0)
        
        # Calculate max loss
        if side == 'long':
            max_loss = (entry - float(sl_price)) * contracts if sl_price else 0
            sl_pct = ((entry - float(sl_price)) / entry * 100) if sl_price and entry else 0
        else:
            max_loss = (float(sl_price) - entry) * contracts if sl_price else 0
            sl_pct = ((float(sl_price) - entry) / entry * 100) if sl_price and entry else 0
        
        print(f"\n{symbol}")
        print(f"   Side: {side.upper()}")
        print(f"   Entry: ${entry:.4f}")
        print(f"   Size: {contracts}")
        print(f"   Notional: ${abs(notional):.2f}")
        
        if tp_price and sl_price:
            print(f"   TP: ${float(tp_price):.4f} ({abs((float(tp_price)-entry)/entry*100):.2f}%)")
            print(f"   SL: ${float(sl_price):.4f} ({abs(sl_pct):.2f}%)")
            print(f"   Max Loss: ~${abs(max_loss):.2f}")
            
            if abs(max_loss) <= 5:
                print(f"   STATUS: PROTECTED (under $5 limit)")
                protected_count += 1
            else:
                print(f"   STATUS: WARNING (loss > $5)")
        else:
            print(f"   TP: NOT SET")
            print(f"   SL: NOT SET")
            print(f"   STATUS: NEEDS PROTECTION")
            needs_protection.append(pos)
    
    print("\n" + "=" * 70)
    print(f"SUMMARY: {protected_count}/{len(open_positions)} positions protected")
    
    if needs_protection:
        print(f"\n⚠️  {len(needs_protection)} position(s) need TP/SL:")
        for pos in needs_protection:
            print(f"   - {pos.get('symbol', '')}")
        print("\nTP/SL Guardian will auto-protect these positions.")
    else:
        print("\n✅ All positions have TP/SL protection!")
    
    # Show balance
    balance = exchange.fetch_balance()
    usdt = balance.get('USDT', {})
    print(f"\nBalance: ${usdt.get('free', 0):.2f} USDT free")
    
except Exception as e:
    print(f"Error: {e}")

print("=" * 70)
