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

positions = exchange.fetch_positions()
active_positions = []
for pos in positions:
    if float(pos.get('contracts', 0)) != 0:
        active_positions.append({
            'symbol': pos.get('symbol'),
            'side': pos.get('side'),
            'entryPrice': pos.get('entryPrice'),
            'markPrice': pos.get('markPrice'),
            'contracts': pos.get('contracts'),
            'unrealizedPnl': pos.get('unrealizedPnl'),
            'percentage': pos.get('percentage'),
            'leverage': pos.get('leverage'),
            'liquidationPrice': pos.get('liquidationPrice')
        })

print(json.dumps(active_positions, indent=2))
