from alpaca.trading.client import TradingClient
from alpaca.trading.requests import StopLossRequest, TakeProfitRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

with open('../.alpaca_env', 'r') as f:
    lines = f.read().strip().split('\n')
    API_KEY = lines[0].strip()
    API_SECRET = lines[1].strip()

client = TradingClient(API_KEY, API_SECRET, paper=True)

print('=== Opening positions with Limit Orders + TP/SL ===')
symbols = ['SPY', 'QQQ', 'NVDA', 'TSLA', 'AAPL', 'MSFT', 'META', 'AMD']
entry_prices = {'SPY': 685, 'QQQ': 605, 'NVDA': 188, 'TSLA': 410, 'AAPL': 263, 'MSFT': 398, 'META': 635, 'AMD': 198}

for sym in symbols:
    try:
        entry = entry_prices.get(sym, 100)
        tp = round(entry * 1.05, 2)
        sl = round(entry * 0.98, 2)
        
        # Use limit order with TP/SL
        order = LimitOrderRequest(
            symbol=sym,
            qty=1,
            side=OrderSide.BUY,
            limit_price=entry,
            time_in_force=TimeInForce.GTC,
            take_profit=TakeProfitRequest(limit_price=tp),
            stop_loss=StopLossRequest(stop_price=sl)
        )
        client.submit_order(order)
        print(f'  [OK] {sym}: Limit ${entry} | TP ${tp} | SL ${sl}')
    except Exception as e:
        print(f'  [X] {sym}: {e}')

print('\n=== Done ===')
