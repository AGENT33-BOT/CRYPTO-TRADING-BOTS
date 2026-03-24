"""
Emergency Close All Positions - Bybit
"""
import ccxt

print("EMERGENCY: Closing ALL positions...")
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
    
    # Fetch all positions
    positions = exchange.fetch_positions()
    
    closed_count = 0
    for pos in positions:
        symbol = pos.get('symbol', '')
        contracts = float(pos.get('contracts', 0))
        side = pos.get('side', '')
        
        if contracts != 0:
            print(f"\n{symbol}")
            print(f"   Side: {side.upper()}")
            print(f"   Size: {contracts}")
            print(f"   PnL: ${pos.get('unrealizedPnl', 0):.2f}")
            
            # Close position
            try:
                if side == 'long':
                    exchange.create_market_sell_order(symbol, contracts)
                    print(f"   CLOSED (Market Sell)")
                else:
                    exchange.create_market_buy_order(symbol, contracts)
                    print(f"   CLOSED (Market Buy)")
                closed_count += 1
            except Exception as e:
                print(f"   Error: {e}")
    
    print("\n" + "=" * 60)
    if closed_count == 0:
        print("No open positions found")
    else:
        print(f"Closed {closed_count} position(s)")
    
    # Get updated balance
    balance = exchange.fetch_balance()
    usdt = balance.get('USDT', {}).get('free', 0)
    print(f"Free Balance: ${usdt:.2f} USDT")
    
except Exception as e:
    print(f"Fatal Error: {e}")

print("\nRemember to stop the bots to prevent new positions!")
