from alpaca.trading.client import TradingClient
from alpaca.trading.requests import StopLossRequest, TakeProfitRequest, MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

with open('../.alpaca_env', 'r') as f:
    lines = f.read().strip().split('\n')
    API_KEY = lines[0].strip()
    API_SECRET = lines[1].strip()

client = TradingClient(API_KEY, API_SECRET, paper=True)

# Get positions
positions = client.get_all_positions()
print(f'=== Setting TP/SL on {len(positions)} Positions ===')

for p in positions:
    symbol = p.symbol
    avg_price = float(p.avg_entry_price)
    qty = float(p.qty)
    
    # Set 5% TP, 2% SL
    tp_price = round(avg_price * 1.05, 2)
    sl_price = round(avg_price * 0.98, 2)
    
    try:
        # Submit bracket order with TP/SL
        order = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            take_profit=TakeProfitRequest(limit_price=tp_price),
            stop_loss=StopLossRequest(stop_price=sl_price)
        )
        result = client.submit_order(order)
        print(f'[OK] {symbol}: Entry ${avg_price} | TP ${tp_price} | SL ${sl_price}')
    except Exception as e:
        print(f'[X] {symbol}: {e}')

print('\n=== Verifying Positions ===')
positions = client.get_all_positions()
for p in positions:
    print(f'{p.symbol}: {p.qty} @ ${float(p.avg_entry_price):.2f}')
