"""
BOSS33 Background Monitor
Monitors BTC position and sends alerts
Created: 2026-02-05
"""

import ccxt
import time
import json
from datetime import datetime

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

# Alert thresholds
ALERT_PROFIT_50 = 0.50  # Alert at +$0.50
ALERT_PROFIT_100 = 1.00  # Alert at +$1.00
ALERT_LOSS_50 = -0.50   # Alert at -$0.50
CHECK_INTERVAL = 30     # Check every 30 seconds

def check_position():
    try:
        exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'linear'}
        })
        
        exchange.load_markets()
        
        # Check BTC position
        positions = exchange.fetch_positions(['BTC/USDT:USDT'])
        
        if positions and len(positions) > 0:
            pos = positions[0]
            size = float(pos.get('contracts', 0))
            
            if size > 0:
                entry = float(pos['entryPrice'])
                mark = float(pos['markPrice'])
                pnl = float(pos['unrealizedPnl'])
                side = pos['side']
                
                # Calculate percentage
                if side == 'long':
                    pnl_pct = ((mark - entry) / entry) * 100
                else:
                    pnl_pct = ((entry - mark) / entry) * 100
                
                return {
                    'symbol': 'BTC/USDT',
                    'side': side,
                    'size': size,
                    'entry': entry,
                    'mark': mark,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'active': True
                }
        
        return {'active': False}
        
    except Exception as e:
        print(f"Error: {e}")
        return {'active': False, 'error': str(e)}

def main():
    print("="*60)
    print("BOSS33 Position Monitor")
    print("Started:", datetime.now().strftime('%H:%M:%S'))
    print("="*60)
    print("\nMonitoring BTC position...")
    print("Will alert on significant changes.\n")
    
    last_pnl = 0
    alerts_sent = set()
    
    try:
        while True:
            position = check_position()
            
            if not position.get('active'):
                print(f"[{datetime.now().strftime('%H:%M:%S')}] No active BTC position")
                time.sleep(CHECK_INTERVAL)
                continue
            
            pnl = position['pnl']
            pnl_pct = position['pnl_pct']
            mark = position['mark']
            
            # Log current status
            status_symbol = "+" if pnl > 0 else "-" if pnl < 0 else "="
            print(f"[{datetime.now().strftime('%H:%M:%S')}] BTC SHORT | Mark: ${mark:,.0f} | PnL: ${pnl:+.2f} ({pnl_pct:+.2f}%)")
            
            # Check for alerts
            alert_msg = None
            
            if pnl >= ALERT_PROFIT_100 and 'profit_100' not in alerts_sent:
                alert_msg = f"🎯 BTC POSITION: +${pnl:.2f} profit reached! Consider taking profits."
                alerts_sent.add('profit_100')
            elif pnl >= ALERT_PROFIT_50 and 'profit_50' not in alerts_sent:
                alert_msg = f"📈 BTC POSITION: +${pnl:.2f} profit - Halfway to target!"
                alerts_sent.add('profit_50')
            elif pnl <= ALERT_LOSS_50 and 'loss_50' not in alerts_sent:
                alert_msg = f"⚠️ BTC POSITION: ${pnl:.2f} loss - Approaching stop loss!"
                alerts_sent.add('loss_50')
            
            if alert_msg:
                print(f"\n{'!'*60}")
                print(alert_msg)
                print(f"{'!'*60}\n")
                
                # Log alert
                with open('monitor_alerts.json', 'a') as f:
                    f.write(json.dumps({
                        'time': datetime.now().isoformat(),
                        'message': alert_msg,
                        'pnl': pnl
                    }) + '\n')
            
            last_pnl = pnl
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\nMonitor stopped by user.")

if __name__ == '__main__':
    main()
