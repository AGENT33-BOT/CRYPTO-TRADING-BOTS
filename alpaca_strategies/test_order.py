from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import os

# Load API keys
with open('../.alpaca_env', 'r') as f:
    lines = f.read().strip().split('\n')
    API_KEY = lines[0].strip()
    API_SECRET = lines[1].strip()

client = TradingClient(API_KEY, API_SECRET, paper=True)

# Get account info
account = client.get_account()
print(f"Equity: ${account.equity}")
print(f"Cash: ${account.cash}")
print(f"Buying Power: ${account.buying_power}")

# Get positions
positions = client.get_all_positions()
print(f"\nOpen Positions: {len(positions)}")
for p in positions:
    print(f"  {p.symbol}: {p.qty} shares @ ${float(p.avg_entry_price):.2f} = ${float(p.market_value):.2f} (PnL: ${float(p.unreal_pl):.2f})")

# Place a simple market order for SPY
print("\nPlacing test order...")
order = MarketOrderRequest(
    symbol="SPY",
    qty=1,
    side=OrderSide.BUY,
    time_in_force=TimeInForce.DAY
)

try:
    result = client.submit_order(order)
    print(f"Order placed: {result.id} - {result.status}")
except Exception as e:
    print(f"Order error: {e}")
