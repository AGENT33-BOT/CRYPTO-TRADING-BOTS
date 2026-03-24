from pybit import usdt_perpetual
import os

s = usdt_perpetual.HTTP('https://api.bybit.com')
r = s.get_wallet_balance(accountType='UNIFIED')
print('Available:', r['result']['list'][0]['totalAvailableBalance'])
print('Total:', r['result']['list'][0]['totalEquity'])
