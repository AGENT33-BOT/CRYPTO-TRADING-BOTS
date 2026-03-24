#!/usr/bin/env python3
"""Quick Alpaca connection test"""
import sys
sys.path.insert(0, '.')
from alpaca_config import ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL

print(f'Base URL: {ALPACA_BASE_URL}')
print(f'Key (first 8 chars): {ALPACA_API_KEY[:8]}...' if ALPACA_API_KEY else 'No key')

try:
    from alpaca.trading.client import TradingClient
    client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True)
    account = client.get_account()
    print(f'\n[OK] Connection successful!')
    print(f'Account ID: {account.id}')
    print(f'Equity: ${account.equity}')
    print(f'Cash: ${account.cash}')
    print(f'Buying Power: ${account.buying_power}')
except ImportError:
    print('[ERROR] alpaca-py not installed')
except Exception as e:
    print(f'[ERROR] {type(e).__name__}: {e}')
