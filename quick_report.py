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
usdt = balance.get('USDT', {})
total = float(usdt.get('total', 0))
free = float(usdt.get('free', 0))
used = float(usdt.get('used', 0))

print(f"BALANCE|{total:.2f}|{free:.2f}|{used:.2f}")

# Get positions
symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'XRP/USDT:USDT', 
           'ADA/USDT:USDT', 'DOGE/USDT:USDT', 'NEAR/USDT:USDT', 'LINK/USDT:USDT',
           'AVAX/USDT:USDT', 'DOT/USDT:USDT', 'APT/USDT:USDT', 'SUI/USDT:USDT']

total_pnl = 0
position_count = 0
positions = []

for symbol in symbols:
    try:
        pos_list = exchange.fetch_positions([symbol])
        for pos in pos_list:
            contracts = float(pos.get('contracts', 0))
            if contracts != 0:
                position_count += 1
                side = pos['side'].upper()
                entry = float(pos.get('entryPrice', 0))
                mark = float(pos.get('markPrice', 0))
                pnl = float(pos.get('unrealizedPnl', 0))
                pnl_pct = ((mark - entry) / entry * 100) if entry > 0 else 0
                total_pnl += pnl
                positions.append({
                    'symbol': symbol.replace('/USDT:USDT', ''),
                    'side': side,
                    'entry': entry,
                    'mark': mark,
                    'size': contracts,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct
                })
    except Exception as e:
        pass

print(f"POSITIONS|{position_count}|{total_pnl:+.2f}")
for p in positions:
    print(f"POS|{p['symbol']}|{p['side']}|{p['entry']:.4f}|{p['mark']:.4f}|{p['size']}|{p['pnl']:+.2f}|{p['pnl_pct']:+.2f}")
