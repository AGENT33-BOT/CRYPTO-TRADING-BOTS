"""
Close orphaned limit/conditional orders when no open position exists for that coin
"""
import ccxt
import time
from datetime import datetime

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

def cleanup_orphaned_orders():
    """Close orders for coins with no open position"""
    
    print("="*60)
    print("ORPHANED ORDER CLEANUP")
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
        # Get open positions
        print("Fetching positions...")
        positions = exchange.fetch_positions()
        open_symbols = set()
        
        for pos in positions:
            contracts = pos.get('contracts', 0) or 0
            if contracts > 0:
                symbol = pos.get('symbol')
                if symbol:
                    open_symbols.add(symbol)
        
        print(f"Symbols with open positions: {len(open_symbols)}")
        for sym in sorted(open_symbols):
            print(f"  - {sym}")
        print()
        
        # Get all open orders
        print("Fetching open orders...")
        symbols_to_check = [
            'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 
            'XRP/USDT:USDT', 'ADA/USDT:USDT', 'DOGE/USDT:USDT',
            'LINK/USDT:USDT', 'NEAR/USDT:USDT', 'AVAX/USDT:USDT',
            'MATIC/USDT:USDT', 'DOT/USDT:USDT', 'LTC/USDT:USDT'
        ]
        
        all_orders = []
        for symbol in symbols_to_check:
            try:
                orders = exchange.fetch_open_orders(symbol)
                all_orders.extend(orders)
                if orders:
                    print(f"  {symbol}: {len(orders)} orders")
            except Exception:
                pass
        
        print(f"\nTotal open orders: {len(all_orders)}")
        
        # Find orphaned orders (no position for that symbol)
        orphaned = []
        for order in all_orders:
            symbol = order.get('symbol')
            if symbol and symbol not in open_symbols:
                orphaned.append(order)
        
        print(f"Orphaned orders (no position): {len(orphaned)}")
        
        # Cancel orphaned orders
        if orphaned:
            print("\nCancelling orphaned orders...")
            cancelled = 0
            for order in orphaned:
                order_id = order.get('id')
                symbol = order.get('symbol', 'N/A')
                side = order.get('side', 'N/A')
                order_type = order.get('type', 'limit')
                
                try:
                    exchange.cancel_order(order_id, symbol)
                    print(f"  CANCELLED: {symbol} {side} {order_type}")
                    cancelled += 1
                    time.sleep(0.5)
                except Exception as e:
                    print(f"  ERROR: {symbol} - {e}")
            
            print(f"\n✓ Cancelled {cancelled} orphaned orders")
        else:
            print("\n✓ No orphaned orders found")
        
        # Summary
        print()
        print("="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Open positions: {len(open_symbols)}")
        print(f"Total orders: {len(all_orders)}")
        print(f"Orphaned orders: {len(orphaned)}")
        print("="*60)
        
        return {
            'positions': len(open_symbols),
            'orders': len(all_orders),
            'orphaned': len(orphaned)
        }
        
    except Exception as e:
        print(f"ERROR: {e}")
        return {'error': str(e)}

if __name__ == "__main__":
    cleanup_orphaned_orders()
