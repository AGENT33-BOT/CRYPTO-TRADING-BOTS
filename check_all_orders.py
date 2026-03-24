"""
Check all orders including conditional/stop orders
"""
import ccxt
from datetime import datetime

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

def check_all_orders():
    """Check all types of orders"""
    
    print("="*60)
    print("FULL ORDER CHECK")
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
        open_positions = []
        for pos in positions:
            contracts = pos.get('contracts', 0) or 0
            if contracts > 0:
                open_positions.append({
                    'symbol': pos.get('symbol'),
                    'side': pos.get('side'),
                    'contracts': contracts
                })
        
        print(f"Open positions: {len(open_positions)}")
        for p in open_positions:
            print(f"  - {p['symbol']}: {p['side']} {p['contracts']} contracts")
        print()
        
        # Get open orders (limit orders)
        print("Fetching OPEN orders (limit)...")
        symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 
                   'XRP/USDT:USDT', 'ADA/USDT:USDT', 'DOGE/USDT:USDT',
                   'LINK/USDT:USDT', 'NEAR/USDT:USDT', 'AVAX/USDT:USDT',
                   'MATIC/USDT:USDT', 'DOT/USDT:USDT', 'LTC/USDT:USDT',
                   'BCH/USDT:USDT', 'ETC/USDT:USDT', 'FIL/USDT:USDT']
        
        open_orders = []
        for symbol in symbols:
            try:
                orders = exchange.fetch_open_orders(symbol)
                open_orders.extend(orders)
                if orders:
                    print(f"  {symbol}: {len(orders)} orders")
            except Exception:
                pass
        
        print(f"\nTotal OPEN orders: {len(open_orders)}")
        
        # Group orders by symbol
        orders_by_symbol = {}
        for order in open_orders:
            symbol = order.get('symbol', 'Unknown')
            if symbol not in orders_by_symbol:
                orders_by_symbol[symbol] = []
            orders_by_symbol[symbol].append({
                'id': order.get('id'),
                'side': order.get('side'),
                'type': order.get('type'),
                'price': order.get('price'),
                'amount': order.get('amount')
            })
        
        print("\nOrders by symbol:")
        for symbol, orders in orders_by_symbol.items():
            has_position = any(p['symbol'] == symbol for p in open_positions)
            status = "HAS POSITION" if has_position else "NO POSITION"
            print(f"\n  {symbol} ({len(orders)} orders) - {status}")
            for o in orders:
                print(f"    - {o['side']} {o['type']} @ {o['price']} x {o['amount']}")
        
        # Summary
        print()
        print("="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Open positions: {len(open_positions)}")
        position_symbols = {p['symbol'] for p in open_positions}
        print(f"Position symbols: {position_symbols}")
        print(f"\nTotal open orders: {len(open_orders)}")
        
        # Find orphaned orders
        orphaned_symbols = set(orders_by_symbol.keys()) - position_symbols
        orphaned_orders = []
        for sym in orphaned_symbols:
            orphaned_orders.extend(orders_by_symbol[sym])
        
        print(f"\nOrders on symbols WITHOUT positions: {len(orphaned_orders)}")
        for sym in orphaned_symbols:
            print(f"  - {sym}: {len(orders_by_symbol[sym])} orders (ORPHANED)")
        
        print("="*60)
        
        return {
            'positions': len(open_positions),
            'position_symbols': list(position_symbols),
            'total_orders': len(open_orders),
            'orphaned_orders': len(orphaned_orders),
            'orphaned_symbols': list(orphaned_symbols)
        }
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}

if __name__ == "__main__":
    check_all_orders()
