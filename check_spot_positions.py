"""
Check and Close All SPOT Positions on Bybit
"""
import ccxt

print("=" * 70)
print("CHECKING FOR SPOT POSITIONS - BYBIT MAIN ACCOUNT")
print("=" * 70)

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

try:
    exchange.load_markets()
    
    # Fetch spot balance
    balance = exchange.fetch_balance()
    
    print("\nSPOT BALANCES:")
    print("-" * 70)
    
    # Get USDT balance
    usdt_total = balance.get('USDT', {}).get('total', 0)
    usdt_free = balance.get('USDT', {}).get('free', 0)
    
    print(f"USDT: {usdt_total}")
    print(f"Free: {usdt_free}")
    
    # Check for other coins
    print("\nOther coins with balance:")
    found = False
    for symbol, data in balance.items():
        if symbol in ['info', 'USDT', 'free', 'used', 'total']:
            continue
        try:
            if isinstance(data, dict):
                total = data.get('total', 0)
                if total and float(total) > 0:
                    print(f"  {symbol}: {total}")
                    found = True
        except:
            pass
    
    if not found:
        print("  None found")
    
    # Check for open spot orders
    print("\n" + "=" * 70)
    print("CHECKING OPEN SPOT ORDERS:")
    print("-" * 70)
    
    try:
        orders = exchange.fetch_open_orders()
        if orders:
            print(f"\nFound {len(orders)} open spot order(s):")
            for order in orders:
                print(f"  {order['symbol']}: {order['side']} {order['amount']} @ {order['price']}")
        else:
            print("\nNO OPEN SPOT ORDERS")
    except Exception as e:
        print(f"\nCould not fetch orders: {e}")
    
    print("\n" + "=" * 70)
    if not found:
        print("RESULT: NO SPOT POSITIONS FOUND")
    else:
        print("RESULT: Found spot positions - see above")
    print("=" * 70)
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
