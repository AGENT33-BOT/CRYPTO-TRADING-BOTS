"""
BOSS33 Position Monitor
Monitors existing positions, no new entries
Created: 2026-02-05
"""

import ccxt
import time
from datetime import datetime

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

def monitor_positions():
    try:
        exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'linear'}
        })
        
        exchange.load_markets()
        
        symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT', 'DOGE/USDT:USDT']
        total_pnl = 0
        
        print(f"\n{'='*60}")
        print(f"Position Monitor - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}\n")
        
        for symbol in symbols:
            positions = exchange.fetch_positions([symbol])
            if positions and len(positions) > 0:
                pos = positions[0]
                size = float(pos.get('contracts', 0))
                
                if size > 0:
                    side = pos['side']
                    entry = float(pos['entryPrice'])
                    mark = float(pos['markPrice'])
                    pnl = float(pos['unrealizedPnl'])
                    total_pnl += pnl
                    
                    # Calculate %
                    if side == 'long':
                        pnl_pct = ((mark - entry) / entry) * 100
                    else:
                        pnl_pct = ((entry - mark) / entry) * 100
                    
                    status = "PROFIT" if pnl > 0 else "LOSS" if pnl < -0.05 else "FLAT"
                    icon = "+" if pnl > 0 else "-" if pnl < -0.05 else "="
                    
                    print(f"{icon} {symbol} [{side.upper()}]")
                    print(f"   Size: {size} | Entry: ${entry:,.2f} | Mark: ${mark:,.2f}")
                    print(f"   PnL: ${pnl:+.2f} ({pnl_pct:+.2f}%) - {status}")
                    print()
        
        # Get balance
        balance = exchange.fetch_balance()
        free = float(balance.get('USDT', {}).get('free', 0))
        total = float(balance.get('USDT', {}).get('total', 0))
        
        print(f"{'='*60}")
        print(f"Total PnL: ${total_pnl:+.2f}")
        print(f"Balance: ${total:.2f} (Free: ${free:.2f})")
        print(f"{'='*60}")
        
        # Check BTC ticker for context
        try:
            ticker = exchange.fetch_ticker('BTC/USDT:USDT')
            change = ticker.get('percentage', 0)
            print(f"\nBTC Market: ${ticker['last']:,.0f} ({change:+.2f}% 24h)")
        except:
            pass
        
        return total_pnl
        
    except Exception as e:
        print(f"Error: {e}")
        return 0

if __name__ == '__main__':
    print("="*60)
    print("BOSS33 Position Monitor")
    print("Monitoring mode - No new entries")
    print("="*60)
    print("\nPress Ctrl+C to stop\n")
    
    try:
        while True:
            pnl = monitor_positions()
            
            if pnl <= -2.0:
                print("\n⚠️ WARNING: Total loss exceeds -$2.00")
            elif pnl >= 5.0:
                print("\n🎯 TARGET HIT: Total profit +$5.00 - Consider taking profits!")
            
            print(f"\nNext check in 60 seconds...\n")
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\n\nMonitor stopped.")
