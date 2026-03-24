from alpaca.trading.client import TradingClient
from alpaca.trading.enums import AccountStatus
import os
from dotenv import load_dotenv

load_dotenv('.alpaca_env')

client = TradingClient(os.getenv('APCA_API_KEY_ID'), os.getenv('APCA_API_SECRET_KEY'), paper=True)
account = client.get_account()

print('=== ALPACA ACCOUNT STATUS ===')
print(f'Status: {account.status}')
print(f'Cash: ${float(account.cash):,.2f}')
print(f'Portfolio Value: ${float(account.portfolio_value):,.2f}')
print(f'Buying Power: ${float(account.buying_power):,.2f}')
print(f'Pattern Day Trader: {account.pattern_day_trader}')
print(f'Trading Blocked: {account.trading_blocked}')
print(f'Transfers Blocked: {account.transfers_blocked}')

# Get positions
positions = client.get_all_positions()
print(f'\n=== POSITIONS ({len(positions)}) ===')
if positions:
    for p in positions:
        print(f'  {p.symbol}: {p.qty} shares @ ${float(p.avg_entry_price):.2f} = ${float(p.market_value):.2f} (P&L: ${float(p.unrealized_pl):.2f})')
else:
    print('  No open positions')
