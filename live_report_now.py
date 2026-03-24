import ccxt
import socket
socket.setdefaulttimeout(15)

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'},
    'timeout': 15000
})

print('='*60)
print('BYBIT HOURLY REPORT - Feb 9, 2025 12:15 PM ET')
print('='*60)

try:
    balance = exchange.fetch_balance()
    usdt = balance.get('USDT', {})
    total = float(usdt.get('total', 0))
    free = float(usdt.get('free', 0))
    print(f'\nBALANCE: ${total:.2f} USDT')
    print(f'Available: ${free:.2f} USDT')
except Exception as e:
    print(f'Error: {e}')
    total = 0

print('\nChecking positions...')
symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE', 'NEAR', 'LINK', 'AVAX', 'DOT', 'APT', 'SUI']
positions = []
total_pnl = 0

for sym in symbols:
    try:
        pos = exchange.fetch_positions([f'{sym}/USDT:USDT'])
        if pos and float(pos[0].get('contracts', 0)) != 0:
            p = pos[0]
            pnl = float(p.get('unrealizedPnl', 0))
            total_pnl += pnl
            positions.append({
                'symbol': sym,
                'side': p['side'].upper(),
                'pnl': pnl
            })
    except:
        pass

if positions:
    print(f'\nOPEN POSITIONS ({len(positions)}):')
    for p in positions:
        status = '+' if p['pnl'] >= 0 else '-'
        print(f'   {status} {p["symbol"]} {p["side"]}: ${p["pnl"]:+.2f}')
    print(f'\nTotal Unrealized PnL: ${total_pnl:+.2f}')
    print(f'Account Value: ~${total + total_pnl:.2f} USDT')
else:
    print('\nNo open positions')

print('='*60)
