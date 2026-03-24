from alpaca.trading.client import TradingClient

with open('../.alpaca_env', 'r') as f:
    lines = f.read().strip().split('\n')
    API_KEY = lines[0].strip()
    API_SECRET = lines[1].strip()

client = TradingClient(API_KEY, API_SECRET, paper=True)

# Get all orders
orders = client.get_orders()
print('=== All Orders ===')
for o in orders:
    tp = o.take_profit_limit_price if o.take_profit_limit_price else 'N/A'
    sl = o.stop_loss_stop_price if o.stop_loss_stop_price else 'N/A'
    print(f'{o.symbol}: {o.side} {o.qty} @ {o.type} | Status: {o.status}')
    print(f'  TP: {tp} | SL: {sl}')
