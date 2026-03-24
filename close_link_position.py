"""
Close LINK Position to Free Up Balance
"""
import ccxt

print("=" * 60)
print("CLOSING LINK POSITION")
print("=" * 60)

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
    
    # Get LINK position
    symbol = 'LINK/USDT:USDT'
    positions = exchange.fetch_positions([symbol])
    
    for pos in positions:
        contracts = float(pos.get('contracts', 0))
        side = pos.get('side', '')
        pnl = float(pos.get('unrealizedPnl', 0))
        
        if contracts != 0:
            print(f"\nPosition Found:")
            print(f"  Symbol: {symbol}")
            print(f"  Side: {side.upper()}")
            print(f"  Size: {contracts}")
            print(f"  P&L: ${pnl:.2f}")
            
            # Close position (market order opposite direction)
            print(f"\nClosing position...")
            if side == 'long':
                order = exchange.create_market_sell_order(symbol, contracts)
            else:
                order = exchange.create_market_buy_order(symbol, contracts)
            
            print(f"  CLOSED! Order ID: {order.get('id', 'N/A')}")
            
    # Get updated balance
    balance = exchange.fetch_balance()
    usdt = balance.get('USDT', {})
    print(f"\n" + "=" * 60)
    print(f"Updated Balance:")
    print(f"  Total: ${usdt.get('total', 0):.2f} USDT")
    print(f"  Free: ${usdt.get('free', 0):.2f} USDT")
    print(f"  Used: ${usdt.get('used', 0):.2f} USDT")
    
except Exception as e:
    print(f"Error: {e}")

print("=" * 60)
