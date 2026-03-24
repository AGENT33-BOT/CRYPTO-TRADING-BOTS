"""
Sell All SPOT Holdings for USDT
"""
import ccxt

print("=" * 70)
print("SELLING ALL SPOT HOLDINGS FOR USDT")
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
    
    # Get balance
    balance = exchange.fetch_balance()
    
    # Coins to sell (exclude USDT)
    coins_to_sell = ['ETH', 'SOL', 'XRP', 'ADA', 'LINK', 'DOGE']
    
    total_usdt_before = float(balance.get('USDT', {}).get('free', 0))
    print(f"\nUSDT before: {total_usdt_before:.2f}")
    print("\n" + "-" * 70)
    
    sold = []
    failed = []
    
    for coin in coins_to_sell:
        try:
            amount = balance.get(coin, {}).get('free', 0)
            if float(amount) <= 0:
                continue
                
            symbol = f"{coin}/USDT"
            
            # Check if market exists
            if symbol not in exchange.markets:
                print(f"\n{coin}: Market not found")
                failed.append(coin)
                continue
            
            print(f"\n{coin}: Selling {amount}...")
            
            # Create market sell order
            order = exchange.create_market_sell_order(symbol, amount)
            
            print(f"  SOLD! Order ID: {order.get('id', 'N/A')}")
            sold.append(coin)
            
        except Exception as e:
            print(f"  FAILED: {e}")
            failed.append(coin)
    
    # Get final balance
    print("\n" + "=" * 70)
    final_balance = exchange.fetch_balance()
    total_usdt_after = float(final_balance.get('USDT', {}).get('free', 0))
    
    print(f"\nUSDT after: {total_usdt_after:.2f}")
    print(f"Gain: {total_usdt_after - total_usdt_before:.2f} USDT")
    
    print(f"\nSold: {len(sold)} coins ({', '.join(sold)})")
    if failed:
        print(f"Failed: {len(failed)} coins ({', '.join(failed)})")
    
    print("\n" + "=" * 70)
    print("All spot holdings converted to USDT!")
    print("=" * 70)
    
except Exception as e:
    print(f"\nFatal error: {e}")
    import traceback
    traceback.print_exc()
