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

# Get balance
balance = exchange.fetch_balance()
print('=== BALANCE ===')
print(f"USDT Free: ${balance.get('USDT', {}).get('free', 0)}")
print(f"USDT Total: ${balance.get('USDT', {}).get('total', 0)}")

# Get positions
print('\n=== POSITIONS ===')
for symbol in ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']:
    try:
        pos_list = exchange.fetch_positions([symbol])
        if pos_list and len(pos_list) > 0:
            pos = pos_list[0]
            contracts = float(pos.get('contracts', 0))
            if contracts > 0:
                entry = float(pos.get('entryPrice', 0))
                mark = float(pos.get('markPrice', 0))
                pnl = float(pos.get('unrealizedPnl', 0))
                side = pos['side']
                print(f"{symbol}: {side.upper()} | Size: {contracts} | Entry: ${entry:.2f} | Mark: ${mark:.2f} | PnL: ${pnl:+.2f}")
    except Exception as e:
        print(f'{symbol}: Error - {e}')
