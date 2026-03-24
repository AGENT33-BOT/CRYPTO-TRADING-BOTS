"""
Check Bybit positions and balance
"""
import ccxt
import json

# Load API credentials from auto_trader_enhanced.py or use hardcoded
API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

# Connect to Bybit
exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

print("="*60)
print("BYBIT ACCOUNT STATUS")
print("="*60)
print()

# Get balance
try:
    balance = exchange.fetch_balance()
    usdt = balance.get('USDT', {})
    total = float(usdt.get('total', 0))
    free = float(usdt.get('free', 0))
    used = float(usdt.get('used', 0))
    
    print("BALANCE:")
    print(f"   Total: ${total:.2f} USDT")
    print(f"   Available: ${free:.2f} USDT")
    print(f"   Used in Positions: ${used:.2f} USDT")
    print()
except Exception as e:
    print(f"Error fetching balance: {e}")

# Get positions
print("OPEN POSITIONS:")
print("-"*60)

try:
    symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'XRP/USDT:USDT', 
               'ADA/USDT:USDT', 'DOGE/USDT:USDT', 'NEAR/USDT:USDT', 'LINK/USDT:USDT',
               'AVAX/USDT:USDT', 'DOT/USDT:USDT', 'APT/USDT:USDT', 'SUI/USDT:USDT']
    
    total_pnl = 0
    position_count = 0
    
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
                    pnl_pct = float(pos.get('percentage', 0))
                    total_pnl += pnl
                    
                    status = "+" if pnl >= 0 else "-"
                    print(f"{status} {symbol}")
                    print(f"   Side: {side}")
                    print(f"   Entry: ${entry:.4f}")
                    print(f"   Mark: ${mark:.4f}")
                    print(f"   Size: {contracts}")
                    print(f"   PnL: ${pnl:+.2f} ({pnl_pct:+.2f}%)")
                    print()
        except:
            pass
    
    print("-"*60)
    print(f"Total Positions: {position_count}")
    print(f"Total Unrealized PnL: ${total_pnl:+.2f}")
    
except Exception as e:
    print(f"Error fetching positions: {e}")

print()
print("="*60)
