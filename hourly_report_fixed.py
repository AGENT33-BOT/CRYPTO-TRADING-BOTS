import ccxt
import socket
import os

# Set shorter timeouts
socket.setdefaulttimeout(10)

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'},
    'timeout': 10000
})

# Enable UTF-8 for Windows
os.system('chcp 65001 >nul 2>&1')

print("="*60)
print("BYBIT HOURLY REPORT - Feb 9, 2026 9:21 AM ET")
print("="*60)
print()

# Get balance
try:
    balance = exchange.fetch_balance()
    usdt = balance.get('USDT', {})
    total = float(usdt.get('total', 0))
    free = float(usdt.get('free', 0))
    used = float(usdt.get('used', 0))
    
    print("BALANCE")
    print(f"   Total: ${total:.2f} USDT")
    print(f"   Available: ${free:.2f} USDT")
    print(f"   Used: ${used:.2f} USDT")
    print()
except Exception as e:
    print(f"Balance error: {e}")
    total = 0

# Get positions
try:
    symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'XRP/USDT:USDT', 
               'ADA/USDT:USDT', 'DOGE/USDT:USDT', 'NEAR/USDT:USDT', 'LINK/USDT:USDT',
               'AVAX/USDT:USDT', 'DOT/USDT:USDT', 'APT/USDT:USDT', 'SUI/USDT:USDT']
    
    total_pnl = 0
    positions = []
    
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
    
    print(f"OPEN POSITIONS ({len(positions)})")
    print("-"*60)
    
    if positions:
        for pos in positions:
            status = "+" if pos['pnl'] >= 0 else "-"
            print(f"{status} {pos['symbol']} {pos['side']}")
            print(f"   Size: {pos['size']} | Entry: ${pos['entry']:.4f} | Mark: ${pos['mark']:.4f}")
            print(f"   PnL: ${pos['pnl']:+.2f} ({pos['pnl_pct']:+.2f}%)")
            print()
    else:
        print("   No open positions")
        print()
    
    print("-"*60)
    print(f"Total Unrealized PnL: ${total_pnl:+.2f}")
    
except Exception as e:
    print(f"Positions error: {e}")
    total_pnl = 0

print()
print("="*60)
print("SUMMARY")
print(f"   Account Value: ~${total + total_pnl:.2f} USDT")
print("="*60)
