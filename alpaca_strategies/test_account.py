from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

with open('../.alpaca_env', 'r') as f:
    lines = f.read().strip().split('\n')
    API_KEY = lines[0].strip()
    API_SECRET = lines[1].strip()

client = TradingClient(API_KEY, API_SECRET, paper=True)

# Check account
account = client.get_account()
print(f'Account:')
print(f'  Cash: ${account.cash}')
print(f'  Buying Power: ${account.buying_power}')
print(f'  Day Trading BP: ${account.daytrading_buying_power}')
print(f'  Pattern Day Trader: {account.pattern_day_trader}')
print(f'  Trading Blocked: {account.trading_blocked}')
print(f'  Transfers Blocked: {account.transfers_blocked}')

# Try simple market order for 1 share
print('\nTrying simple market order...')
try:
    order = MarketOrderRequest(symbol='SPY', qty=1, side=OrderSide.BUY, time_in_force=TimeInForce.DAY)
    result = client.submit_order(order)
    print(f'Order placed: {result.id} - {result.status}')
except Exception as e:
    print(f'Error: {e}')
