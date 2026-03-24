from alpaca.trading.client import TradingClient
from alpaca.trading.requests import StopLossRequest, TakeProfitRequest, MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import time

with open('../.alpaca_env', 'r') as f:
    lines = f.read().strip().split('\n')
    API_KEY = lines[0].strip()
    API_SECRET = lines[1].strip()

client = TradingClient(API_KEY, API_SECRET, paper=True)

# Close all positions first
positions = client.get_all_positions()
print(f'=== Closing {len(positions)} positions ===')
for p in positions:
    try:
        order = MarketOrderRequest(symbol=p.symbol, qty=p.qty, side=OrderSide.SELL, time_in_force=TimeInForce.DAY)
        client.submit_order(order)
        print(f'  SOLD {p.symbol}')
    except Exception as e:
        print(f'  Error {p.symbol}: {e}')

time.sleep(2)

# Reopen with TP/SL
print('\n=== Reopening with TP/SL (5% TP, 2% SL) ===')
symbols = ['SPY', 'QQQ', 'NVDA', 'TSLA', 'AAPL', 'MSFT', 'META', 'AMD']
entry_prices = {'SPY': 687, 'QQQ': 607, 'NVDA': 190, 'TSLA': 412, 'AAPL': 265, 'MSFT': 400, 'META': 638, 'AMD': 200}

for sym in symbols:
    try:
        entry = entry_prices.get(sym, 100)
        tp = round(entry * 1.05, 2)
        sl = round(entry * 0.98, 2)
        
        order = MarketOrderRequest(
            symbol=sym,
            qty=1,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            take_profit=TakeProfitRequest(limit_price=tp),
            stop_loss=StopLossRequest(stop_price=sl)
        )
        client.submit_order(order)
        print(f'  [OK] {sym}: Entry ${entry} | TP ${tp} | SL ${sl}')
    except Exception as e:
        print(f'  [X] {sym}: {e}')

print('\n=== Done ===')
