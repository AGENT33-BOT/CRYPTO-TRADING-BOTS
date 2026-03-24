from alpaca.trading.client import TradingClient
from alpaca_config import ALPACA_API_KEY, ALPACA_SECRET_KEY

client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True)
account = client.get_account()
print(f'API Connected!')
print(f'Account: {account.account_number}')
print(f'Cash: ${float(account.cash):.2f}')
print(f'Equity: ${float(account.equity):.2f}')
