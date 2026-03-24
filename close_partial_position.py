"""
Bybit Position Manager - Close 50% NEAR Position
Created: 2026-02-05
Purpose: Take partial profits on winning trade
"""

import ccxt
import os
import json
from datetime import datetime

# API Credentials
API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

def close_partial_position(symbol='NEAR/USDT:USDT', percentage=50):
    """Close a percentage of an open position"""
    
    try:
        # Initialize Bybit exchange
        exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'linear',  # USDT Perpetual
            }
        })
        
        print(f"🔌 Connecting to Bybit...")
        exchange.load_markets()
        
        # Get current position
        print(f"📊 Checking {symbol} position...")
        positions = exchange.fetch_positions([symbol])
        
        if not positions:
            print(f"❌ No position found for {symbol}")
            return False
        
        position = positions[0]
        current_size = float(position['contracts'])
        entry_price = float(position['entryPrice'])
        mark_price = float(position['markPrice'])
        side = position['side']  # 'long' or 'short'
        
        if current_size == 0:
            print(f"❌ Position size is 0 - already closed?")
            return False
        
        # Calculate amount to close
        close_size = current_size * (percentage / 100)
        close_size = round(close_size, 4)
        
        print(f"\n📈 Position Details:")
        print(f"   Symbol: {symbol}")
        print(f"   Side: {side.upper()}")
        print(f"   Current Size: {current_size}")
        print(f"   Entry Price: ${entry_price:.4f}")
        print(f"   Mark Price: ${mark_price:.4f}")
        print(f"   PnL: ${position['unrealizedPnl']:.2f}")
        print(f"\n🎯 Closing {percentage}% = {close_size} contracts")
        
        # Confirm with user
        confirm = input(f"\n⚠️  Confirm: Close {close_size} {symbol} at market price? (yes/no): ")
        
        if confirm.lower() != 'yes':
            print("❌ Cancelled by user")
            return False
        
        # Execute market close order
        print(f"\n🚀 Executing market close order...")
        
        # For closing long, we sell. For closing short, we buy
        order_side = 'sell' if side == 'long' else 'buy'
        
        order = exchange.create_market_order(
            symbol=symbol,
            side=order_side,
            amount=close_size,
            params={'reduceOnly': True}  # Ensure it only closes, doesn't open new
        )
        
        print(f"\n✅ ORDER EXECUTED SUCCESSFULLY!")
        print(f"   Order ID: {order['id']}")
        print(f"   Closed: {close_size} {symbol}")
        print(f"   Average Price: ${order['average']:.4f}" if order.get('average') else "   Price: Market")
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Save trade log
        trade_log = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'action': f'close_{percentage}_percent',
            'side': side,
            'amount_closed': close_size,
            'remaining': current_size - close_size,
            'entry_price': entry_price,
            'close_price': order.get('average', mark_price),
            'order_id': order['id']
        }
        
        with open('C:\\Users\\digim\\clawd\\crypto_trader\\partial_close_log.json', 'a') as f:
            f.write(json.dumps(trade_log) + '\n')
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("🤖 Bybit Position Manager - Partial Close")
    print("=" * 60)
    print()
    
    # Close 50% of NEAR position
    success = close_partial_position('NEAR/USDT:USDT', 50)
    
    if success:
        print("\n🎉 Profit secured! Position partially closed.")
    else:
        print("\n⚠️  Operation failed or cancelled.")
