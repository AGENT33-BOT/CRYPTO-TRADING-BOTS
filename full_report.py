import ccxt
import json
from datetime import datetime

print('='*60)
print('AGENT BYBIT - FULL TRADE REPORT')
print(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('='*60)

# ========== MAIN BYBIT ACCOUNT ==========
print('\n[MAIN BYBIT ACCOUNT]')
print('-'*40)

exchange1 = ccxt.bybit({
    'apiKey': 'bsK06QDhsagOWwFsXQ',
    'secret': 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa',
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})
exchange1.set_sandbox_mode(False)

try:
    balance = exchange1.fetch_balance({'type': 'unified'})
    usdt = balance.get('USDT', {})
    print(f"Balance: {usdt.get('total', 0):.2f} USDT")
    print(f"Free: {usdt.get('free', 0):.2f} USDT")
    print(f"Used: {usdt.get('used', 0):.2f} USDT")
except Exception as e:
    print(f"Balance Error: {e}")

# Positions
try:
    positions = exchange1.fetch_positions()
    open_pos = [p for p in positions if float(p.get('contracts', 0)) != 0]
    print(f"\nOpen Positions: {len(open_pos)}")
    
    total_pnl = 0
    missing_tp_sl = []
    
    for pos in open_pos:
        symbol = pos['symbol']
        side = pos['side']
        size = pos['contracts']
        entry = pos['entryPrice']
        pnl = pos['unrealizedPnl']
        total_pnl += float(pnl)
        tp = pos.get('takeProfit', 0)
        sl = pos.get('stopLoss', 0)
        
        print(f"\n  {symbol} {side.upper()}")
        print(f"    Size: {size} | Entry: {entry}")
        print(f"    PnL: {pnl:.4f} USDT")
        print(f"    TP: {tp if tp else 'NOT SET'}")
        print(f"    SL: {sl if sl else 'NOT SET'}")
        
        if not tp or not sl:
            missing_tp_sl.append(symbol)
    
    print(f"\nTotal Unrealized PnL: {total_pnl:.4f} USDT")
    if missing_tp_sl:
        print(f"\n⚠️  MISSING TP/SL: {', '.join(missing_tp_sl)}")
except Exception as e:
    print(f"Positions Error: {e}")

# ========== BYBIT2 ACCOUNT ==========
print('\n\n[BYBIT2 ACCOUNT]')
print('-'*40)

exchange2 = ccxt.bybit({
    'apiKey': 'aLz3ySrF9kMZubmqDR',
    'secret': '8SlpKyX7vleDu1loJiFePGWfnynJRXZXaD2z',
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})
exchange2.set_sandbox_mode(False)

try:
    balance2 = exchange2.fetch_balance({'type': 'unified'})
    usdt2 = balance2.get('USDT', {})
    print(f"Balance: {usdt2.get('total', 0):.2f} USDT")
    print(f"Free: {usdt2.get('free', 0):.2f} USDT")
    print(f"Used: {usdt2.get('used', 0):.2f} USDT")
except Exception as e:
    print(f"Balance Error: {e}")

try:
    positions2 = exchange2.fetch_positions()
    open_pos2 = [p for p in positions2 if float(p.get('contracts', 0)) != 0]
    print(f"\nOpen Positions: {len(open_pos2)}")
    
    total_pnl2 = 0
    missing_tp_sl2 = []
    
    for pos in open_pos2:
        symbol = pos['symbol']
        side = pos['side']
        size = pos['contracts']
        entry = pos['entryPrice']
        pnl = pos['unrealizedPnl']
        total_pnl2 += float(pnl)
        tp = pos.get('takeProfit', 0)
        sl = pos.get('stopLoss', 0)
        
        print(f"\n  {symbol} {side.upper()}")
        print(f"    Size: {size} | Entry: {entry}")
        print(f"    PnL: {pnl:.4f} USDT")
        print(f"    TP: {tp if tp else 'NOT SET'}")
        print(f"    SL: {sl if sl else 'NOT SET'}")
        
        if not tp or not sl:
            missing_tp_sl2.append(symbol)
    
    print(f"\nTotal Unrealized PnL: {total_pnl2:.4f} USDT")
    if missing_tp_sl2:
        print(f"\n⚠️  MISSING TP/SL: {', '.join(missing_tp_sl2)}")
except Exception as e:
    print(f"Positions Error: {e}")

# Running bots check
print('\n\n[RUNNING BOT PROCESSES]')
print('-'*40)
import subprocess
result = subprocess.run(['powershell', '-Command', 'Get-Process python | Select-Object Id, ProcessName, @{N="Runtime";E={[math]::Round(((Get-Date) - $_.StartTime).TotalHours,1)}} | Format-Table -AutoSize'], capture_output=True, text=True)
print(result.stdout if result.stdout else "Could not retrieve process list")

print('\n' + '='*60)
print('END OF REPORT')
print('='*60)
