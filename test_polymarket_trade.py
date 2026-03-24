"""
Polymarket Test Trade Script
Place a small test trade with minimal edge requirements
"""

import sys
sys.path.insert(0, '.')

from polymarket_trader import PolymarketTrader

def place_test_trade():
    """Place a small test trade"""
    
    print("="*60)
    print("POLYMARKET TEST TRADE")
    print("="*60)
    print()
    print("Available opportunities:")
    print()
    
    # Create trader
    trader = PolymarketTrader()
    
    # Get opportunities
    opportunities = trader.find_opportunities()
    
    # Show top 5
    for i, opp in enumerate(opportunities[:5], 1):
        print(f"{i}. {opp['question'][:50]}...")
        print(f"   YES Price: ${opp['yes_price']:.3f}")
        print(f"   Signal: {opp['signal']}")
        print(f"   Edge: {opp['edge']*100:.1f}%")
        print(f"   Volume: ${opp['volume']:,.0f}")
        print()
    
    # Ask which to trade
    choice = input("Select trade (1-5) or 0 to cancel: ").strip()
    
    if choice == "0" or not choice:
        print("Cancelled.")
        return
    
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(opportunities):
            print("Invalid selection.")
            return
        
        selected = opportunities[idx]
        
        print()
        print("="*60)
        print("TRADE DETAILS")
        print("="*60)
        print(f"Market: {selected['question'][:60]}")
        print(f"Signal: {selected['signal']}")
        print(f"Price: ${selected['yes_price']:.3f}")
        print(f"Edge: {selected['edge']*100:.1f}%")
        print()
        
        # Set small test size
        trade_size = float(input("Trade size in USD (min $5, suggest $10-20 for test): ") or "10")
        
        if trade_size < 5:
            print("Minimum trade is $5.")
            return
        
        confirm = input(f"\nPlace ${trade_size:.2f} trade? (yes/no): ").strip().lower()
        
        if confirm == "yes":
            # Override min edge for test
            trader.config['min_edge'] = 0.05  # Lower to 5% for test
            
            result = trader.execute_trade(selected)
            
            if result:
                print()
                print("="*60)
                print("✅ TEST TRADE EXECUTED!")
                print("="*60)
                print(f"Size: ${trade_size:.2f}")
                print(f"Market: {selected['question'][:50]}...")
                print()
                print("Check your Polymarket portfolio to confirm.")
            else:
                print()
                print("❌ Trade failed. Check logs.")
        else:
            print("Cancelled.")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    place_test_trade()
