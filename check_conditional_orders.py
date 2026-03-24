"""
Check conditional orders (stop loss, take profit)
"""
import ccxt
import requests
from datetime import datetime

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

def check_conditional_orders():
    """Check conditional/stop orders via Bybit API"""
    
    print("="*60)
    print("CHECKING CONDITIONAL ORDERS")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print()
    
    exchange = ccxt.bybit({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })
    
    try:
        # Try to get conditional orders via ccxt
        print("Checking for stop/conditional orders...")
        
        symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 
                   'XRP/USDT:USDT', 'ADA/USDT:USDT', 'DOGE/USDT:USDT',
                   'LINK/USDT:USDT', 'NEAR/USDT:USDT', 'AVAX/USDT:USDT',
                   'BCH/USDT:USDT', 'ETC/USDT:USDT', 'APT/USDT:USDT']
        
        total_conditional = 0
        
        for symbol in symbols:
            try:
                # Try to fetch conditional orders
                orders = exchange.fetch_open_orders(symbol, params={'stop': True})
                if orders:
                    print(f"  {symbol}: {len(orders)} conditional orders")
                    for o in orders:
                        print(f"    - {o.get('type')} {o.get('side')} @ trigger: {o.get('triggerPrice', 'N/A')}")
                    total_conditional += len(orders)
            except Exception as e:
                # Try alternative method
                try:
                    orders = exchange.fetch_orders(symbol, params={'stopOrderStatus': 'Untriggered'})
                    if orders:
                        print(f"  {symbol}: {len(orders)} untriggered stop orders")
                        total_conditional += len(orders)
                except:
                    pass
        
        print(f"\nTotal conditional orders: {total_conditional}")
        
        # Also check positions with attached stops
        print("\nChecking positions for attached TP/SL...")
        positions = exchange.fetch_positions()
        for pos in positions:
            contracts = pos.get('contracts', 0) or 0
            if contracts > 0:
                symbol = pos.get('symbol')
                tp = pos.get('takeProfitPrice', 'None')
                sl = pos.get('stopLossPrice', 'None')
                print(f"  {symbol}: TP={tp}, SL={sl}")
        
        print("\n" + "="*60)
        print(f"Total conditional/stop orders found: {total_conditional}")
        print("="*60)
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_conditional_orders()
