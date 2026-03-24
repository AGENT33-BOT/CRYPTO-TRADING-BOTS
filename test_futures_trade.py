# Test Trade Script - Futures XRP/USDT with 3x Leverage
import ccxt
import time

# API Credentials
API_KEY = "bsK06QDhsagOWwFsXQ"
API_SECRET = "ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa"

def test_futures_trade():
    print("="*60)
    print("BYBIT FUTURES TEST - XRP/USDT PERP (3x LEVERAGE)")
    print("="*60)
    
    # Connect to Bybit Futures
    exchange = ccxt.bybit({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future',  # Futures trading
            'adjustForTimeDifference': True
        }
    })
    
    symbol = 'XRP/USDT:USDT'  # Perpetual futures
    leverage = 3
    
    try:
        # Get balance
        balance = exchange.fetch_balance()
        usdt = balance.get('USDT', {}).get('free', 0)
        print(f"\nBalance: ${usdt:.2f} USDT (Available for margin)")
        
        # Get XRP price
        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        print(f"XRP Perp Price: ${price:.4f}")
        
        # Set leverage to 3x
        print(f"\nSetting leverage to {leverage}x...")
        try:
            exchange.set_leverage(leverage, symbol)
            print(f"Leverage set to {leverage}x")
        except Exception as e:
            print(f"Leverage already set or error: {e}")
        
        # Calculate position size
        # With 3x leverage, $5 margin = $15 position
        margin_amount = min(usdt * 0.10, 5.0)  # Use 10% of balance or $5 max
        position_value = margin_amount * leverage
        amount = position_value / price
        
        print(f"\nTest Trade:")
        print(f"  Margin: ${margin_amount:.2f}")
        print(f"  Leverage: {leverage}x")
        print(f"  Position Value: ${position_value:.2f}")
        print(f"  XRP Amount: {amount:.2f}")
        print("="*60)
        
        # OPEN LONG POSITION
        print("\nSTEP 1: OPENING LONG POSITION...")
        buy_order = exchange.create_market_buy_order(symbol, amount)
        print(f"LONG POSITION OPENED")
        print(f"   Entry: ${price:.4f}")
        print(f"   Size: {amount:.4f} XRP")
        print(f"   Margin: ${margin_amount:.2f}")
        
        # Wait a moment
        print("\nWaiting 5 seconds...")
        time.sleep(5)
        
        # Check position
        positions = exchange.fetch_positions([symbol])
        position = None
        for p in positions:
            if p['symbol'] == symbol and float(p['contracts']) != 0:
                position = p
                break
        
        if position:
            print(f"\nPosition Open:")
            print(f"  Size: {position['contracts']} {position['contractSize']}")
            print(f"  Entry: ${position['entryPrice']:.4f}")
            print(f"  Margin: ${position['collateral']:.2f}")
        
        # CLOSE POSITION (Market Sell)
        print("\nSTEP 2: CLOSING LONG POSITION...")
        sell_order = exchange.create_market_sell_order(symbol, amount)
        
        # Calculate PnL
        buy_price = price
        sell_price = ticker['last']  # Current price
        pnl = (sell_price - buy_price) * amount
        pnl_pct = ((sell_price - buy_price) / buy_price) * 100
        
        print(f"POSITION CLOSED")
        print(f"   Exit: ${sell_price:.4f}")
        
        print("\n" + "="*60)
        print("FUTURES TRADE RESULTS")
        print("="*60)
        print(f"Entry Price:  ${buy_price:.4f}")
        print(f"Exit Price:   ${sell_price:.4f}")
        print(f"Gross PnL:    ${pnl:.4f}")
        print(f"Return:       {pnl_pct:+.2f}%")
        print(f"With {leverage}x Lev: {pnl_pct * leverage:+.2f}% on margin")
        
        # Get final balance
        balance = exchange.fetch_balance()
        final_usdt = balance.get('USDT', {}).get('free', 0)
        print(f"\nFinal Balance: ${final_usdt:.2f} USDT")
        
        print("\nFUTURES TEST TRADE COMPLETE!")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_futures_trade()
    exit(0 if success else 1)
