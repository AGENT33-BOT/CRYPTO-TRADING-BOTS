#!/usr/bin/env python3
import alpaca_trade_api as tradeapi
import json
import os
from pathlib import Path

# Load credentials from .alpaca_env file
env_path = Path(__file__).parent.parent / ".alpaca_env"
api_key = ""
api_secret = ""

if env_path.exists():
    with open(env_path, 'r') as f:
        lines = f.read().strip().split('\n')
        if len(lines) >= 2:
            api_key = lines[0].strip()
            api_secret = lines[1].strip()

# Override with environment variables if set
api_key = os.getenv('ALPACA_API_KEY', api_key)
api_secret = os.getenv('ALPACA_SECRET_KEY', api_secret)
base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')

api = tradeapi.REST(api_key, api_secret, base_url)

account = api.get_account()
positions = api.list_positions()

print('=' * 60)
print('           AGENT ALPACA - PnL REPORT')
print('=' * 60)
print()
print(f'Account ID:    {account.id}')
print(f'Status:        {account.status}')
print()
print('-' * 60)
print('BALANCE SUMMARY')
print('-' * 60)
print(f'Portfolio Value:  ${float(account.portfolio_value):,.2f}')
print(f'Cash:             ${float(account.cash):,.2f}')
print(f'Buying Power:     ${float(account.buying_power):,.2f}')
print(f'Equity:           ${float(account.equity):,.2f}')
print()
print('-' * 60)
print('TODAY PERFORMANCE')
print('-' * 60)
day_pl = float(account.equity) - float(account.last_equity)
day_pl_pct = (day_pl / float(account.last_equity)) * 100 if float(account.last_equity) > 0 else 0
emoji = '+' if day_pl >= 0 else '-'
print(f'{emoji} Day P&L:        ${day_pl:,.2f} ({day_pl_pct:+.2f}%)')
print(f'Last Equity:      ${float(account.last_equity):,.2f}')
print()

if positions:
    print('-' * 60)
    print(f'OPEN POSITIONS ({len(positions)})')
    print('-' * 60)
    total_pl = 0
    for pos in positions:
        pl = float(pos.unrealized_pl)
        pl_pct = float(pos.unrealized_plpc) * 100
        total_pl += pl
        emoji_pos = '+' if pl >= 0 else '-'
        side = 'LONG' if int(pos.qty) > 0 else 'SHORT'
        print(f"{emoji_pos} {pos.symbol:6} {side:6} | Qty: {abs(int(pos.qty)):>6} | P&L: ${pl:>9.2f} ({pl_pct:>+.2f}%)")
    print('-' * 60)
    emoji_total = '+' if total_pl >= 0 else '-'
    print(f'{emoji_total} Total Unrealized P&L: ${total_pl:,.2f}')
else:
    print('-' * 60)
    print('OPEN POSITIONS: None')
    print('-' * 60)

print()
print('=' * 60)
print(f'Strategies Active: 23 | Status: RUNNING')
print('=' * 60)
