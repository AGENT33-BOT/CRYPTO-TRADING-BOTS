import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

bybit = ccxt.bybit({
    'apiKey': os.getenv('BYBIT_API_KEY'),
    'secret': os.getenv('BYBIT_API_SECRET'),
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

print("="*60)
print("CHECKING POSITIONS WITH TP/SL DETAILS")
print("="*60)

try:
    positions = bybit.fetch_positions()
    for p in positions:
        contracts = float(p.get('contracts', 0) or 0)
        if contracts != 0:
            symbol = p['symbol']
            entry = p.get('entryPrice', 'N/A')
            size = p.get('contracts', 'N/A')
            notional = p.get('notional', 'N/A')
            pnl = p.get('unrealizedPnl', 'N/A')
            tp = p.get('takeProfitPrice') or p.get('info', {}).get('takeProfit', 'NOT SET')
            sl = p.get('stopLossPrice') or p.get('info', {}).get('stopLoss', 'NOT SET')
            
            print(f"\n{symbol}")
            print(f"  Entry: ${entry}")
            print(f"  Size: {size}")
            print(f"  Notional: ${float(notional):.2f}" if notional != 'N/A' else "  Notional: N/A")
            print(f"  PnL: ${float(pnl):.2f}" if pnl != 'N/A' else "  PnL: N/A")
            print(f"  TP: {tp}")
            print(f"  SL: {sl}")
            
            if tp == 'NOT SET' or sl == 'NOT SET' or tp == '0' or sl == '0':
                print(f"  ⚠️  WARNING: TP/SL NOT SET!")
            else:
                print(f"  ✅ TP/SL properly configured")
    
    # Also check open orders
    print("\n" + "="*60)
    print("OPEN ORDERS (Conditional TP/SL)")
    print("="*60)
    orders = bybit.fetch_open_orders()
    if orders:
        for o in orders:
            print(f"{o['symbol']}: {o['type']} @ {o.get('triggerPrice', o['price'])}")
    else:
        print("No open orders found")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
