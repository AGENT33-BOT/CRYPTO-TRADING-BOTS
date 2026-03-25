import requests
import hmac
import hashlib
import time
import json

api_key = 'KfmiIdWd16hG18v2O7'
api_secret = 'VTVePZIz2GEqyy6AcvwPVcaRNBRolmXkuWlZ'

ts = str(int(time.time() * 1000))
endpoint = '/v5/position/closed-pnl'

params = {'category': 'linear', 'limit': 50}

# Sign with proper JSON formatting (no spaces after separators)
param_str = json.dumps(params, separators=(',', ':'))
msg = ts + api_key + endpoint + param_str
sign = hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).hexdigest()

headers = {
    'X-BAPI-API-KEY': api_key,
    'X-BAPI-SIGN': sign,
    'X-BAPI-TIMESTAMP': ts,
    'Content-Type': 'application/json'
}

r = requests.get('https://api.bybit.com' + endpoint, params=params, headers=headers, timeout=10)
result = r.json()

if result.get('retCode') != 0:
    print('Error:', result.get('retMsg'))
    exit()

data = result.get('result', {}).get('list', [])

print('=== BYBIT TRADING HISTORY ===')
print()

# Group by symbol
stats = {}
for p in data:
    pnl = float(p.get('closedPnl', 0))
    sym = p.get('symbol', '').replace('USDT','')
    
    if sym not in stats:
        stats[sym] = {'wins':0,'losses':0,'total_pnl':0,'trades':0}
    
    stats[sym]['total_pnl'] += pnl
    stats[sym]['trades'] += 1
    if pnl > 0:
        stats[sym]['wins'] += 1
    else:
        stats[sym]['losses'] += 1

# Sort by PnL
sorted_stats = sorted(stats.items(), key=lambda x: x[1]['total_pnl'], reverse=True)

print('=== PERFORMANCE BY PAIR ===')
total_all = 0
for sym, d in sorted_stats:
    wr = (d['wins'] / d['trades'] * 100) if d['trades'] > 0 else 0
    print(f'{sym}:')
    print(f'  Trades: {d["trades"]} | Wins: {d["wins"]} | Losses: {d["losses"]}')
    print(f'  Win Rate: {wr:.0f}%')
    print(f'  PnL: ${d["total_pnl"]:.2f}')
    print()
    total_all += d['total_pnl']

print('=== OVERALL ===')
wins_total = sum(d['wins'] for _,d in sorted_stats)
losses_total = sum(d['losses'] for _,d in sorted_stats)
trades_total = sum(d['trades'] for _,d in sorted_stats)
print(f'Total Trades: {trades_total}')
print(f'Total Wins: {wins_total} | Losses: {losses_total}')
print(f'Overall Win Rate: {wins_total/trades_total*100:.0f}%')
print(f'Total PnL: ${total_all:.2f}')