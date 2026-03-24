import ccxt

exchange = ccxt.bybit({
    'apiKey': 'bsK06QDhsagOWwFsXQ',
    'apiSecret': 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa',
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

try:
    balance = exchange.fetch_balance()
    usdt = balance.get('USDT', {})
    total = float(usdt.get('total', 0))
    free = float(usdt.get('free', 0))
    used = float(usdt.get('used', 0))
    print('BALANCE|total:{}|free:{}|used:{}'.format(round(total,2), round(free,2), round(used,2)))
except Exception as e:
    print('BALANCE_ERROR|{}'.format(e))

symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'XRP/USDT:USDT', 
           'ADA/USDT:USDT', 'DOGE/USDT:USDT', 'NEAR/USDT:USDT', 'LINK/USDT:USDT',
           'AVAX/USDT:USDT', 'DOT/USDT:USDT', 'APT/USDT:USDT', 'SUI/USDT:USDT']

positions = []
total_pnl = 0

for symbol in symbols:
    try:
        pos_list = exchange.fetch_positions([symbol])
        for pos in pos_list:
            contracts = float(pos.get('contracts', 0))
            if contracts != 0:
                pnl = float(pos.get('unrealizedPnl', 0))
                total_pnl += pnl
                positions.append({
                    'symbol': symbol.replace('/USDT:USDT', ''),
                    'side': pos['side'].upper(),
                    'size': contracts,
                    'entry': float(pos.get('entryPrice', 0)),
                    'mark': float(pos.get('markPrice', 0)),
                    'pnl': pnl,
                    'pnl_pct': float(pos.get('percentage', 0))
                })
    except:
        pass

print('POSITIONS|count:{}|total_pnl:{}'.format(len(positions), round(total_pnl,2)))
for p in positions:
    print('POS|{}|{}|{}|{:.4f}|{:.4f}|{:+.2f}|{:+.2f}'.format(
        p['symbol'], p['side'], p['size'], p['entry'], p['mark'], p['pnl'], p['pnl_pct']
    ))
