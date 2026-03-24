"""
Continuous Position Monitor - Updates every 30 seconds
"""

import ccxt
import time
from datetime import datetime

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT',
           'DOGE/USDT:USDT', 'XRP/USDT:USDT', 'BCH/USDT:USDT']

print("=" * 60)
print("CONTINUOUS POSITION MONITOR")
print("Updates every 30 seconds - Press Ctrl+C to stop")
print("=" * 60)

try:
    while True:
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        try:
            # Get balance
            balance_info = exchange.fetch_balance()
            free_balance = float(balance_info['USDT']['free'])
            total_balance = float(balance_info['USDT']['total'])
            
            # Count positions
            active_positions = []
            total_pnl = 0
            
            for symbol in symbols:
                try:
                    positions = exchange.fetch_positions([symbol])
                    if positions and len(positions) > 0:
                        pos = positions[0]
                        contracts = float(pos.get('contracts', 0))
                        if contracts > 0:
                            entry = float(pos.get('entryPrice', 0))
                            mark = float(pos.get('markPrice', 0))
                            pnl = float(pos.get('unrealizedPnl', 0))
                            side = pos['side'].upper()
                            active_positions.append({
                                'symbol': symbol.replace('/USDT:USDT', ''),
                                'side': side,
                                'size': contracts,
                                'entry': entry,
                                'mark': mark,
                                'pnl': pnl
                            })
                            total_pnl += pnl
                except:
                    pass
            
            # Clear screen and print update
            print(f"\n[{timestamp}] Balance: ${total_balance:.2f} | Free: ${free_balance:.2f}")
            print(f"Positions: {len(active_positions)}/5 | Total PnL: ${total_pnl:+.2f}")
            
            if active_positions:
                print("-" * 50)
                for pos in active_positions:
                    status = "🟢" if pos['pnl'] >= 0 else "🔴"
                    print(f"{status} {pos['symbol']} {pos['side']} | "
                          f"Entry: ${pos['entry']:.2f} | Mark: ${pos['mark']:.2f} | "
                          f"PnL: ${pos['pnl']:+.2f}")
            else:
                print("No active positions - Scanning for opportunities...")
            
            print("-" * 50)
            
        except Exception as e:
            print(f"[{timestamp}] Error: {e}")
        
        time.sleep(30)
        
except KeyboardInterrupt:
    print("\n\nMonitoring stopped.")
