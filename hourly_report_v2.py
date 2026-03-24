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

print("="*60)
print("BYBIT HOURLY REPORT - Feb 10, 2026 2:21 AM ET")
print("="*60)
print()

# Get balance
balance = exchange.fetch_balance()
usdt = balance.get('USDT', {})
total = float(usdt.get('total', 0))
free = float(usdt.get('free', 0))
used = float(usdt.get('used', 0))

print("ACCOUNT BALANCE")
print(f"   Total:     ${total:.2f} USDT")
print(f"   Available: ${free:.2f} USDT")
print(f"   In Use:    ${used:.2f} USDT")
print()

# Get all positions
print("OPEN POSITIONS")
print("-"*60)

symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'XRP/USDT:USDT', 
           'ADA/USDT:USDT', 'DOGE/USDT:USDT', 'NEAR/USDT:USDT', 'LINK/USDT:USDT',
           'AVAX/USDT:USDT', 'DOT/USDT:USDT', 'APT/USDT:USDT', 'SUI/USDT:USDT']

total_pnl = 0
position_count = 0
positions_list = []

for symbol in symbols:
    try:
        positions = exchange.fetch_positions([symbol])
        for pos in positions:
            contracts = float(pos.get('contracts', 0))
            if contracts != 0:
                position_count += 1
                side = pos['side'].upper()
                entry = float(pos.get('entryPrice', 0))
                mark = float(pos.get('markPrice', 0))
                pnl = float(pos.get('unrealizedPnl', 0))
                pnl_pct = float(pos.get('percentage', 0)) if pos.get('percentage') else ((mark - entry) / entry * 100) if entry > 0 else 0
                total_pnl += pnl
                
                positions_list.append({
                    'symbol': symbol.replace('/USDT:USDT', ''),
                    'side': side,
                    'entry': entry,
                    'mark': mark,
                    'size': contracts,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct
                })
                
                status = "+" if pnl >= 0 else "-"
                print(f"{status} {symbol.replace('/USDT:USDT', '')} {side}")
                print(f"   Entry: ${entry:.4f} -> Mark: ${mark:.4f}")
                print(f"   Size: {contracts} | PnL: ${pnl:+.2f} ({pnl_pct:+.2f}%)")
                print()
    except Exception as e:
        pass

print("-"*60)
print(f"Total Positions: {position_count}")
print(f"Total Unrealized PnL: ${total_pnl:+.2f}")
print()
print("="*60)
print("BOT STATUS: Automated trading active")
print("Strategy: 1.5% TP / 2% SL with ISOLATED 3x leverage")
print("="*60)
