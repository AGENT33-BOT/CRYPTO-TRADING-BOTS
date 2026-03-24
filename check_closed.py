import json
with open('trade_execution_log.json') as f:
    data = json.load(f)
recent = [t for t in data if t.get('status')=='closed'][-5:]
print(f'Recent closed trades: {len(recent)}')
for t in recent:
    print(f'  {t["symbol"]}: PnL {t.get("pnl","N/A")}')