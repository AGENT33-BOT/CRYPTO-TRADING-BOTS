"""
Check open positions and cancel orphaned limit orders
When a position is closed, cancel any associated limit orders
"""
import ccxt
import time
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

def check_and_cleanup():
    """Check positions and cancel orphaned orders"""
    
    print("="*60)
    print("POSITION & ORDER CLEANUP CHECK")
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
        # Fetch positions
        print("Fetching open positions...")
        positions = exchange.fetch_positions()
        open_positions = [p for p in positions if p.get('contracts', 0) > 0]
        
        print(f"Open positions: {len(open_positions)}")
        for pos in open_positions:
            symbol = pos.get('symbol', 'N/A')
            side = pos.get('side', 'N/A')
            contracts = pos.get('contracts', 0)
            pnl = pos.get('unrealizedPnl', 0)
            print(f"  - {symbol}: {side} {contracts} contracts | PnL: ${pnl:.2f}")
        print()
        
        # Fetch open orders
        print("Fetching open orders...")
        all_orders = []
        symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 
                   'XRP/USDT:USDT', 'ADA/USDT:USDT', 'DOGE/USDT:USDT',
                   'LINK/USDT:USDT', 'NEAR/USDT:USDT']
        
        for symbol in symbols:
            try:
                orders = exchange.fetch_open_orders(symbol)
                all_orders.extend(orders)
            except Exception as e:
                pass  # Skip if no orders for this symbol
        
        print(f"Open orders: {len(all_orders)}")
        
        # Get symbols with open positions
        position_symbols = {p.get('symbol') for p in open_positions}
        
        # Find orphaned orders (orders for symbols with no open position)
        orphaned_orders = []
        for order in all_orders:
            order_symbol = order.get('symbol')
            if order_symbol not in position_symbols:
                orphaned_orders.append(order)
        
        print(f"Orphaned orders (no position): {len(orphaned_orders)}")
        
        if orphaned_orders:
            print("\nCancelling orphaned orders...")
            for order in orphaned_orders:
                order_id = order.get('id')
                symbol = order.get('symbol', 'N/A')
                side = order.get('side', 'N/A')
                amount = order.get('amount', 0)
                
                try:
                    exchange.cancel_order(order_id, symbol)
                    print(f"  CANCELLED: {symbol} {side} {amount}")
                    time.sleep(0.5)
                except Exception as e:
                    print(f"  ERROR cancelling {order_id}: {e}")
            
            print(f"\nCancelled {len(orphaned_orders)} orphaned orders")
        else:
            print("No orphaned orders found")
        
        # Summary
        print()
        print("="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Open positions: {len(open_positions)}")
        print(f"Total open orders: {len(all_orders)}")
        print(f"Orphaned orders cancelled: {len(orphaned_orders)}")
        print(f"Active orders remaining: {len(all_orders) - len(orphaned_orders)}")
        print("="*60)
        
        return {
            'open_positions': len(open_positions),
            'open_orders': len(all_orders),
            'orphaned_cancelled': len(orphaned_orders)
        }
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}

if __name__ == "__main__":
    check_and_cleanup()
