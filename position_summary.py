import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

symbols = ['SOL/USDT:USDT', 'ADA/USDT:USDT', 'AVAX/USDT:USDT', 
           'LINK/USDT:USDT', 'DOGE/USDT:USDT']

print('=' * 60)
print('ALL POSITIONS SUMMARY')
print('=' * 60)

total_pnl = 0
for symbol in symbols:
    try:
        pos_list = exchange.fetch_positions([symbol])
        if pos_list and len(pos_list) > 0:
            pos = pos_list[0]
            contracts = float(pos.get('contracts', 0))
            if contracts > 0:
                entry = float(pos.get('entryPrice', 0))
                mark = float(pos.get('markPrice', 0))
                pnl = float(pos.get('unrealizedPnl', 0))
                side = pos['side'].upper()
                total_pnl += pnl
                
                marker = '[LONG]' if side == 'LONG' else '[SHORT]'
                print(f"\n{marker} {symbol}")
                print(f"  Entry: ${entry:.4f}")
                print(f"  Mark: ${mark:.4f}")
                print(f"  Size: {contracts}")
                print(f"  PnL: ${pnl:+.2f}")
    except Exception as e:
        pass

print('\n' + '=' * 60)
print(f'Total Unrealized PnL: ${total_pnl:+.2f}')
print('=' * 60)

balance = exchange.fetch_balance()
print(f"Balance: ${float(balance.get('USDT', {}).get('total', 0)):.2f} USDT")
print(f"Free: ${float(balance.get('USDT', {}).get('free', 0)):.2f} USDT")
