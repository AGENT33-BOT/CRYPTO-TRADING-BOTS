"""
Quick test of PolymarketTrader initialization
"""
from polymarket_trader import PolymarketTrader

# Test paper trading mode (default)
trader = PolymarketTrader()
print("[OK] Paper trading mode initialized successfully")
print(f"Paper trading enabled: {trader.paper_trading}")

# Test with explicit paper mode
trader2 = PolymarketTrader(paper_trading=True)
print(f"[OK] Explicit paper mode: {trader2.paper_trading}")

print("\nAll tests passed!")
