"""
HOLD Strategy Monitor - Market Recovery Mode
Monitors positions during market crash, manages risk
Created: 2026-02-05
"""

import ccxt
import time
import json
from datetime import datetime

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

class HoldStrategyMonitor:
    def __init__(self):
        self.exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'linear'}
        })
        self.max_loss_threshold = -0.50  # Alert if total loss exceeds $0.50
        self.recovery_target = 0.01  # Close at +1% profit
        
    def check_positions(self):
        """Monitor all positions"""
        try:
            symbols = ['ADA/USDT:USDT', 'DOGE/USDT:USDT', 'NEAR/USDT:USDT']
            total_pnl = 0
            position_data = []
            
            print(f"\n{'='*60}")
            print(f"HOLD Strategy Monitor - {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*60}\n")
            
            for symbol in symbols:
                positions = self.exchange.fetch_positions([symbol])
                if positions and positions[0]['contracts'] > 0:
                    pos = positions[0]
                    size = float(pos['contracts'])
                    entry = float(pos['entryPrice'])
                    mark = float(pos['markPrice'])
                    pnl = float(pos['unrealizedPnl'])
                    side = pos['side']
                    total_pnl += pnl
                    
                    position_data.append({
                        'symbol': symbol,
                        'side': side,
                        'size': size,
                        'entry': entry,
                        'mark': mark,
                        'pnl': pnl
                    })
                    
                    status_icon = "🟢" if pnl > 0 else "🔴" if pnl < -0.10 else "🟡"
                    print(f"{status_icon} {symbol}:")
                    print(f"   Size: {size} | Entry: ${entry:.4f} | Mark: ${mark:.4f}")
                    print(f"   PnL: ${pnl:+.2f}")
                    
                    # Check if position hit recovery target
                    if pnl > self.recovery_target:
                        print(f"   ✅ HIT +$0.50 PROFIT TARGET - Consider closing")
                    # Check if position hit max loss
                    elif pnl < -0.30:
                        print(f"   ⚠️  LOSS EXCEEDS -$0.30 - Monitor closely")
            
            print(f"\n💰 Total Unrealized PnL: ${total_pnl:+.2f}")
            
            # Get account balance
            balance = self.exchange.fetch_balance()
            free_usdt = float(balance.get('USDT', {}).get('free', 0))
            print(f"💵 Free USDT: ${free_usdt:.2f}")
            
            # Market snapshot
            print(f"\n📊 Market Status:")
            try:
                btc_ticker = self.exchange.fetch_ticker('BTC/USDT:USDT')
                btc_change = btc_ticker.get('percentage', 0)
                print(f"   BTC: ${btc_ticker['last']:,.0f} ({btc_change:+.2f}% 24h)")
            except:
                pass
                
            # Alert logic
            if total_pnl < self.max_loss_threshold:
                print(f"\n🚨 ALERT: Total loss exceeds ${self.max_loss_threshold}!")
                print(f"   Consider closing positions to limit losses.")
            elif total_pnl > 1.00:
                print(f"\n🎉 PROFIT ALERT: Total profit exceeds $1.00!")
                print(f"   Consider taking some profits.")
            else:
                print(f"\n⏳ Holding... Waiting for market recovery.")
                
            return position_data, total_pnl
            
        except Exception as e:
            print(f"Error: {e}")
            return [], 0
    
    def run(self):
        print("="*60)
        print("HOLD STRATEGY ACTIVATED")
        print("="*60)
        print("\nStrategy:")
        print("  - HOLD current positions")
        print("  - Alert if loss exceeds -$0.50")
        print("  - Alert if profit exceeds +$1.00")
        print("  - Check every 30 seconds")
        print("\nPress Ctrl+C to stop\n")
        
        try:
            while True:
                self.check_positions()
                print(f"\nNext check in 30 seconds...")
                time.sleep(30)
        except KeyboardInterrupt:
            print("\n\nMonitor stopped.")

if __name__ == '__main__':
    monitor = HoldStrategyMonitor()
    monitor.run()
