from alpaca.trading.client import TradingClient
from alpaca.trading.requests import StopLossRequest, TakeProfitRequest, MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import time

with open('../.alpaca_env', 'r') as f:
    lines = f.read().strip().split('\n')
    API_KEY = lines[0].strip()
    API_SECRET = lines[1].strip()

client = TradingClient(API_KEY, API_SECRET, paper=True)

# Get current positions
positions = client.get_all_positions()
print(f'=== Re-opening {len(positions)} Positions with TP/SL ===')

for p in positions:
    symbol = p.symbol
    qty = float(p.qty)
    avg_price = float(p.avg_entry_price)
    
    # Calculate TP/SL prices
    tp_price = round(avg_price * 1.05, 2)
    sl_price = round(avg_price * 0.98, 2)
    
    try:
        # First close the position
        close_order = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY
        )
        client.submit_order(close_order)
        print(f'[SOLD] {symbol} {qty} @ market')
        time.sleep(0.5)  # Wait for fill
        
        # Then reopen with TP/SL
        open_order = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            take_profit=TakeProfitRequest(limit_price=tp_price),
            stop_loss=StopLossRequest(stop_price=sl_price)
        )
        result = client.submit_order(open_order)
        print(f'  -> [OPENED] {symbol} with TP: ${tp_price}, SL: ${sl_price}')
        
    except Exception as e:
        print(f'[X] {symbol}: {e}')

print('\n=== Done ===')
