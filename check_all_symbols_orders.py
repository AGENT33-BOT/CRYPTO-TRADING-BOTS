"""
Comprehensive order check - all symbols
"""
import ccxt
from datetime import datetime

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

def comprehensive_order_check():
    """Check ALL symbols for orders"""
    
    print("="*60)
    print("COMPREHENSIVE ORDER CHECK")
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
        # Get positions
        print("Fetching positions...")
        positions = exchange.fetch_positions()
        position_symbols = set()
        for pos in positions:
            contracts = pos.get('contracts', 0) or 0
            if contracts > 0:
                position_symbols.add(pos.get('symbol'))
        
        print(f"Symbols with positions: {position_symbols}")
        print()
        
        # Extended symbol list
        all_symbols = [
            'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 
            'XRP/USDT:USDT', 'ADA/USDT:USDT', 'DOGE/USDT:USDT',
            'LINK/USDT:USDT', 'NEAR/USDT:USDT', 'AVAX/USDT:USDT',
            'MATIC/USDT:USDT', 'DOT/USDT:USDT', 'LTC/USDT:USDT',
            'BCH/USDT:USDT', 'ETC/USDT:USDT', 'FIL/USDT:USDT',
            'APT/USDT:USDT', 'ARB/USDT:USDT', 'OP/USDT:USDT',
            'SUI/USDT:USDT', 'SEI/USDT:USDT', 'TIA/USDT:USDT',
            'INJ/USDT:USDT', 'RNDR/USDT:USDT', 'FET/USDT:USDT',
            'PEPE/USDT:USDT', 'SHIB/USDT:USDT', 'UNI/USDT:USDT',
            'AAVE/USDT:USDT', 'MKR/USDT:USDT', 'COMP/USDT:USDT'
        ]
        
        all_orders = []
        symbols_with_orders = {}
        
        print("Checking ALL symbols for open orders...")
        for symbol in all_symbols:
            try:
                orders = exchange.fetch_open_orders(symbol)
                if orders:
                    symbols_with_orders[symbol] = orders
                    all_orders.extend(orders)
                    status = "HAS POSITION" if symbol in position_symbols else "NO POSITION"
                    print(f"  {symbol}: {len(orders)} orders - {status}")
            except Exception as e:
                pass
        
        print()
        print("="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Total symbols checked: {len(all_symbols)}")
        print(f"Symbols with orders: {len(symbols_with_orders)}")
        print(f"TOTAL OPEN ORDERS: {len(all_orders)}")
        print()
        
        # Show all orders
        print("ALL ORDERS BREAKDOWN:")
        for symbol, orders in symbols_with_orders.items():
            has_pos = symbol in position_symbols
            status = "(HAS POSITION)" if has_pos else "(ORPHANED)"
            print(f"\n{symbol} {status}:")
            for o in orders:
                print(f"  - {o.get('side')} {o.get('type')} @ {o.get('price')} x {o.get('amount')}")
        
        # Find orphaned
        orphaned = {s: o for s, o in symbols_with_orders.items() if s not in position_symbols}
        print()
        print("="*60)
        print(f"ORPHANED ORDERS: {sum(len(o) for o in orphaned.values())}")
        for s, o in orphaned.items():
            print(f"  {s}: {len(o)} orders")
        print("="*60)
        
        return {
            'total_orders': len(all_orders),
            'symbols_with_orders': len(symbols_with_orders),
            'orphaned_count': sum(len(o) for o in orphaned.values()),
            'orphaned_symbols': list(orphaned.keys())
        }
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}

if __name__ == "__main__":
    comprehensive_order_check()
