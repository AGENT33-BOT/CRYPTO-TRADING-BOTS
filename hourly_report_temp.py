import ccxt
import json

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

print('='*50)
print('BYBIT HOURLY REPORT - Feb 10, 2026 11:21 AM ET')
print('='*50)
print()

# Get balance
balance = exchange.fetch_balance()
usdt = balance.get('USDT', {})
total = float(usdt.get('total', 0))
free = float(usdt.get('free', 0))
used = float(usdt.get('used', 0))

print('ACCOUNT BALANCE')
print(f'   Total:     ${total:.2f} USDT')
print(f'   Available: ${free:.2f} USDT')
print(f'   In Use:    ${used:.2f} USDT')
print()

# Get positions
print('OPEN POSITIONS')
print('-'*50)

positions = exchange.fetch_positions()
total_pnl = 0
position_count = 0

for pos in positions:
    contracts = float(pos.get('contracts', 0))
    if contracts != 0:
        position_count += 1
        side = pos['side'].upper()
        entry = float(pos.get('entryPrice', 0))
        mark = float(pos.get('markPrice', 0))
        pnl = float(pos.get('unrealizedPnl', 0))
        symbol = pos.get('symbol', 'UNKNOWN')
        total_pnl += pnl
        
        status = '+' if pnl >= 0 else '-'
        print(f'{status} {symbol} {side}')
        print(f'   Entry: ${entry:.4f} -> Mark: ${mark:.4f}')
        print(f'   Size: {contracts} | PnL: ${pnl:+.2f}')
        print()

print('-'*50)
print(f'Total Positions: {position_count}')
print(f'Total Unrealized PnL: ${total_pnl:+.2f}')
print()
print('='*50)
