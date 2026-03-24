import requests
import hmac
import hashlib
import time
import json

api_key = 'KfmiIdWd16hG18v2O7'
api_secret = 'VTVePZIz2GEqyy6AcvwPVcaRNBRolmXkuWlZ'

ts = str(int(time.time() * 1000))
endpoint = '/v5/position/closed-pnl'

params = {'category': 'linear', 'limit': 20}

msg = ts + api_key + endpoint + json.dumps(params)
sign = hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).hexdigest()

headers = {
    'X-BAPI-API-KEY': api_key,
    'X-BAPI-SIGN': sign,
    'X-BAPI-TIMESTAMP': ts,
    'Content-Type': 'application/json'
}

r = requests.get('https://api.bybit.com' + endpoint, params=params, headers=headers)
data = r.json().get('result', {}).get('list', [])

print('=== BYBIT TRADING HISTORY ===')
total_pnl = 0
wins = 0
losses = 0

for p in data:
    pnl = float(p.get('closedPnl', 0))
    total_pnl += pnl
    if pnl > 0:
        wins += 1
    else:
        losses += 1
    sym = p.get('symbol', '')
    tm = p.get('updatedTime', '')[:8]
    print(f'{sym} | PnL: {pnl:+.2f} USD | {tm}')

print(f'\n=== SUMMARY ===')
print(f'Total Trades: {len(data)}')
print(f'Wins: {wins} | Losses: {losses}')
if data:
    print(f'Win Rate: {wins/len(data)*100:.1f}%')
print(f'Total PnL: {total_pnl:+.2f} USD')
