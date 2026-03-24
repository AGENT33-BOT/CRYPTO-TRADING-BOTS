from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Load API keys
with open('../.alpaca_env', 'r') as f:
    lines = f.read().strip().split('\n')
    API_KEY = lines[0].strip()
    API_SECRET = lines[1].strip()

client = TradingClient(API_KEY, API_SECRET, paper=True)

# Get account
account = client.get_account()
print(f"Equity: ${account.equity} | Cash: ${account.cash} | BP: ${account.buying_power}")

# Place orders for multiple strong stocks
symbols = ['SPY', 'QQQ', 'NVDA', 'TSLA', 'AAPL', 'MSFT', 'META', 'AMD']
print("\nPlacing orders...")
for sym in symbols:
    try:
        order = MarketOrderRequest(
            symbol=sym,
            qty=1,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY
        )
        result = client.submit_order(order)
        print(f"  BUY {sym}: {result.status}")
    except Exception as e:
        print(f"  Error {sym}: {e}")

# Check positions
print("\nPositions after orders:")
positions = client.get_all_positions()
for p in positions:
    print(f"  {p.symbol}: {p.qty} @ ${float(p.avg_entry_price):.2f}")
