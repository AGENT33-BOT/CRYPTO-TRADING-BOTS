# Test Trade Script - Buy and Sell XRP/USDT
import ccxt
import time

# API Credentials
API_KEY = "bsK06QDhsagOWwFsXQ"
API_SECRET = "ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa"

def test_trade():
    print("="*60)
    print("BYBIT TEST TRADE - XRP/USDT")
    print("="*60)
    
    # Connect to Bybit
    exchange = ccxt.bybit({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
    
    try:
        # Get balance
        balance = exchange.fetch_balance()
        usdt = balance.get('USDT', {}).get('free', 0)
        print(f"\nBalance: ${usdt:.2f} USDT")
        
        # Get XRP price
        ticker = exchange.fetch_ticker('XRP/USDT')
        price = ticker['last']
        print(f"XRP Price: ${price:.4f}")
        
        # Calculate small position (5% of balance, max $5)
        position_value = min(usdt * 0.05, 5.0)
        amount = position_value / price
        
        print(f"\nTest Trade Amount: ${position_value:.2f} ({amount:.2f} XRP)")
        print("="*60)
        
        # BUY XRP
        print("\nSTEP 1: BUYING XRP...")
        buy_order = exchange.create_market_buy_order('XRP/USDT', amount)
        buy_price = buy_order['price'] if buy_order['price'] else buy_order['average']
        print(f"BUY EXECUTED")
        print(f"   Price: ${buy_price:.4f}")
        print(f"   Amount: {amount:.4f} XRP")
        print(f"   Cost: ${position_value:.2f}")
        
        # Wait a moment
        print("\nWaiting 5 seconds...")
        time.sleep(5)
        
        # Check position
        balance = exchange.fetch_balance()
        xrp_balance = balance.get('XRP', {}).get('free', 0)
        print(f"\nXRP Balance: {xrp_balance:.4f}")
        
        # SELL XRP (close position)
        print("\nSTEP 2: SELLING XRP...")
        sell_amount = xrp_balance  # Sell all XRP
        sell_order = exchange.create_market_sell_order('XRP/USDT', sell_amount)
        sell_price = sell_order['price'] if sell_order['price'] else sell_order['average']
        
        # Calculate PnL
        pnl = (sell_price - buy_price) * sell_amount
        pnl_pct = ((sell_price - buy_price) / buy_price) * 100
        
        print(f"SELL EXECUTED")
        print(f"   Price: ${sell_price:.4f}")
        print(f"   Amount: {sell_amount:.4f} XRP")
        
        print("\n" + "="*60)
        print("TRADE RESULTS")
        print("="*60)
        print(f"Buy Price:  ${buy_price:.4f}")
        print(f"Sell Price: ${sell_price:.4f}")
        print(f"PnL:        ${pnl:.4f} ({pnl_pct:+.2f}%)")
        
        # Get final balance
        balance = exchange.fetch_balance()
        final_usdt = balance.get('USDT', {}).get('free', 0)
        print(f"\nFinal Balance: ${final_usdt:.2f} USDT")
        
        print("\nTEST TRADE COMPLETE!")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_trade()
    exit(0 if success else 1)
