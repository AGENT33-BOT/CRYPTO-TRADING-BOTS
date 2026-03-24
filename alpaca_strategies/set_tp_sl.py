from alpaca.trading.client import TradingClient
from alpaca.trading.requests import StopLossRequest, TakeProfitRequest
from alpaca.trading.enums import TimeInForce

with open('../.alpaca_env', 'r') as f:
    lines = f.read().strip().split('\n')
    API_KEY = lines[0].strip()
    API_SECRET = lines[1].strip()

client = TradingClient(API_KEY, API_SECRET, paper=True)

# Get positions
positions = client.get_all_positions()
print(f'=== Positions: {len(positions)} ===')

for p in positions:
    symbol = p.symbol
    avg_price = float(p.avg_entry_price)
    qty = float(p.qty)
    
    # Set 5% TP, 2% SL
    tp_price = round(avg_price * 1.05, 2)
    sl_price = round(avg_price * 0.98, 2)
    
    print(f'{symbol}: Entry ${avg_price} | TP ${tp_price} (+5%) | SL ${sl_price} (-2%)')

print('\n=== Setting TP/SL on all positions ===')
# Get all open positions and add TP/SL
for p in positions:
    symbol = p.symbol
    avg_price = float(p.avg_entry_price)
    qty = float(p.qty)
    
    tp_price = round(avg_price * 1.05, 2)
    sl_price = round(avg_price * 0.98, 2)
    
    # Try to replace the order with TP/SL
    try:
        # Get existing orders
        orders = client.get_orders(status='open')
        for order in orders:
            if order.symbol == symbol:
                # Cancel existing order
                client.cancel_order(order.id)
                print(f'Cancelled {symbol} order {order.id}')
        
        # Submit new order with TP/SL
        from alpaca.trading.requests import MarketOrderRequest
        from alpaca.trading.enums import OrderSide
        
        order = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            take_profit=TakeProfitRequest(limit_price=tp_price),
            stop_loss=StopLossRequest(stop_price=sl_price)
        )
        result = client.submit_order(order)
        print(f'✓ {symbol}: TP ${tp_price}, SL ${sl_price}')
    except Exception as e:
        print(f'Error {symbol}: {e}')

print('\nDone!')
