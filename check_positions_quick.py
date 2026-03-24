import ccxt

exchange = ccxt.bybit({
    'apiKey': 'bsK06QDhsagOWwFsXQ',
    'secret': 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa',
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

positions = exchange.fetch_positions()
open_pos = [p for p in positions if p.get('contracts', 0) > 0]

print(f'Open positions: {len(open_pos)}')
for p in open_pos:
    symbol = p['symbol']
    side = p['side']
    contracts = p['contracts']
    pnl = p.get('unrealizedPnl', 0)
    print(f'  {symbol}: {side} {contracts} contracts | PnL: ${pnl:.2f}')
