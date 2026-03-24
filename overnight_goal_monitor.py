"""
Aggressive Overnight Trading Monitor
Targets: Multiple 1.5% wins with 3x leverage to reach $300
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

PAIRS = [
    'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT',
    'DOGE/USDT:USDT', 'XRP/USDT:USDT', 'LINK/USDT:USDT', 'AVAX/USDT:USDT',
    'DOT/USDT:USDT', 'LTC/USDT:USDT', 'BCH/USDT:USDT', 'UNI/USDT:USDT',
    'ATOM/USDT:USDT', 'ETC/USDT:USDT', 'ARB/USDT:USDT', 'OP/USDT:USDT',
    'NEAR/USDT:USDT', 'APT/USDT:USDT', 'SUI/USDT:USDT'
]

GOAL = 300.0  # Target balance
start_balance = 197.94

print("=" * 70)
print("OVERNIGHT AGGRESSIVE TRADING - TARGET: $300")
print("=" * 70)
print(f"Start: ${start_balance:.2f} | Target: ${GOAL:.2f} | Need: +${GOAL-start_balance:.2f}")
print("=" * 70)
print("Strategy: Multiple 1.5% wins with 3x leverage")
print("Risk: Max $5 per position, 2% SL, ISOLATED margin")
print("=" * 70)

try:
    while True:
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Check balance
        try:
            balance = exchange.fetch_balance()
            current = float(balance['USDT']['total'])
            progress = (current - start_balance) / (GOAL - start_balance) * 100
            print(f"\n[{timestamp}] Balance: ${current:.2f} | Progress: {progress:.1f}%")
            
            if current >= GOAL:
                print(f"\n{'='*70}")
                print(f"🎉 GOAL REACHED! ${current:.2f} >= ${GOAL:.2f}")
                print(f"{'='*70}")
                break
        except:
            pass
        
        # Check positions
        try:
            positions = []
            for symbol in PAIRS[:10]:  # Check main pairs
                pos_list = exchange.fetch_positions([symbol])
                if pos_list and len(pos_list) > 0:
                    p = pos_list[0]
                    if float(p.get('contracts', 0)) > 0:
                        positions.append({
                            'symbol': symbol.replace('/USDT:USDT', ''),
                            'pnl': float(p.get('unrealizedPnl', 0))
                        })
            
            if positions:
                total_pnl = sum(p['pnl'] for p in positions)
                print(f"Positions: {len(positions)} | Unrealized PnL: ${total_pnl:+.2f}")
        except:
            pass
        
        time.sleep(60)  # Check every minute
        
except KeyboardInterrupt:
    print("\n\nOvernight monitoring stopped.")
