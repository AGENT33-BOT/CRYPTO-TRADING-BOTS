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

result = {"balance": {}, "positions": []}

try:
    balance = exchange.fetch_balance()
    usdt = balance.get('USDT', {})
    result["balance"] = {
        "total": float(usdt.get('total', 0)),
        "free": float(usdt.get('free', 0)),
        "used": float(usdt.get('used', 0))
    }
except Exception as e:
    result["balance_error"] = str(e)

try:
    symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'XRP/USDT:USDT', 
               'ADA/USDT:USDT', 'DOGE/USDT:USDT', 'NEAR/USDT:USDT', 'LINK/USDT:USDT',
               'AVAX/USDT:USDT', 'DOT/USDT:USDT', 'APT/USDT:USDT', 'SUI/USDT:USDT']
    
    for symbol in symbols:
        try:
            positions = exchange.fetch_positions([symbol])
            for pos in positions:
                contracts = float(pos.get('contracts', 0))
                if contracts != 0:
                    result["positions"].append({
                        "symbol": symbol,
                        "side": pos['side'].upper(),
                        "entry": float(pos.get('entryPrice', 0)),
                        "mark": float(pos.get('markPrice', 0)),
                        "size": contracts,
                        "pnl": float(pos.get('unrealizedPnl', 0)),
                        "pnl_pct": float(pos.get('percentage', 0))
                    })
        except:
            pass
except Exception as e:
    result["positions_error"] = str(e)

with open('bybit_report.json', 'w') as f:
    json.dump(result, f, indent=2)

print(json.dumps(result, indent=2))
