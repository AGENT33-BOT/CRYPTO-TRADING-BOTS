"""
Close Position Script for Bybit
Quickly close a specific position at market price
"""

import ccxt
import sys

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

def close_position(symbol):
    """Close position at market price"""
    try:
        exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
        
        # Load markets first
        exchange.load_markets()
        
        # Get current position
        positions = exchange.fetch_positions([symbol])
        
        for pos in positions:
            size = float(pos.get('contracts', 0))
            side = pos.get('side', '')
            
            if size > 0:
                # Determine close side
                close_side = 'sell' if side == 'long' else 'buy'
                
                print(f"Closing {symbol} {side} position: {size} contracts")
                
                # Cancel any existing orders first
                try:
                    exchange.cancel_all_orders(symbol)
                    print(f"Cancelled open orders for {symbol}")
                except:
                    pass
                
                # Close at market
                order = exchange.create_order(
                    symbol=symbol,
                    type='market',
                    side=close_side,
                    amount=size,
                    params={'reduceOnly': True}
                )
                
                print(f"✅ Position closed: {order['id']}")
                print(f"   Realized P&L: ${pos.get('unrealizedPnl', 0):.2f}")
                return True
        
        print(f"❌ No open position found for {symbol}")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python close_position.py <SYMBOL>")
        print("Example: python close_position.py NEAR/USDT:USDT")
        sys.exit(1)
    
    symbol = sys.argv[1]
    close_position(symbol)
