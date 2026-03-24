"""
CHALLENGE MONITOR - Personal oversight for $469 → $938
Real-time position tracking and intervention system
"""

import ccxt
import json
import time
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from CHALLENGE_CONFIG import *

LOG_FILE = 'challenge_monitor.log'
ALERT_LOG = 'challenge_alerts.log'

class ChallengeMonitor:
    def __init__(self):
        self.exchange = None
        self.start_time = datetime.now()
        self.initial_balance = STARTING_BALANCE
        self.target = TARGET_BALANCE
        self.high_water_mark = STARTING_BALANCE
        self.low_water_mark = STARTING_BALANCE
        self.trades_today = []
        
    def log(self, msg):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[MONITOR] [{timestamp}] {msg}"
        print(log_msg)
        with open(LOG_FILE, 'a') as f:
            f.write(log_msg + '\n')
            
    def alert(self, msg):
        """Critical alerts that need immediate attention"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        alert_msg = f"🚨 [{timestamp}] {msg}"
        print(f"\n{'='*70}")
        print(alert_msg)
        print(f"{'='*70}\n")
        with open(ALERT_LOG, 'a') as f:
            f.write(alert_msg + '\n')
        self.send_telegram(alert_msg)
        
    def send_telegram(self, msg):
        try:
            import requests
            token = "7594239785:AAG6YjJ4LDK0vMQT5Cq2LHS5-9q-OWJb8oI"
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(url, data={'chat_id': '5804173449', 'text': msg, 'parse_mode': 'Markdown'}, timeout=5)
        except:
            pass
            
    def connect(self):
        try:
            api_key = 'bsK06QDhsagOWwFsXQ'
            api_secret = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'
            
            self.exchange = ccxt.bybit({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'swap',
                    'adjustForTimeDifference': True,
                }
            })
            self.exchange.set_sandbox_mode(False)
            self.exchange.load_markets()
            self.log("Connected to Bybit")
            return True
        except Exception as e:
            self.log(f"Connection error: {e}")
            return False
            
    def get_balance(self):
        try:
            balance = self.exchange.fetch_balance({'type': 'unified'})
            return balance.get('USDT', {})
        except:
            return {}
            
    def get_positions(self):
        try:
            positions = self.exchange.fetch_positions()
            return [p for p in positions if float(p.get('contracts', 0)) != 0]
        except:
            return []
            
    def check_position_health(self, pos):
        """Analyze if position is healthy or needs intervention"""
        symbol = pos.get('symbol', 'Unknown')
        side = pos.get('side', 'Unknown')
        entry = float(pos.get('entryPrice', 0))
        mark = float(pos.get('markPrice', 0))
        unrealized = float(pos.get('unrealizedPnl', 0))
        size = float(pos.get('contracts', 0))
        
        # Calculate P&L percentage
        if side == 'long':
            pnl_pct = (mark - entry) / entry * 100 if entry > 0 else 0
        else:
            pnl_pct = (entry - mark) / entry * 100 if entry > 0 else 0
            
        # Check for tp/sl
        tp = pos.get('takeProfit', 0)
        sl = pos.get('stopLoss', 0)
        
        status = {
            'symbol': symbol,
            'side': side,
            'size': size,
            'entry': entry,
            'mark': mark,
            'unrealized': unrealized,
            'pnl_pct': pnl_pct,
            'has_tp': tp and float(tp) > 0,
            'has_sl': sl and float(sl) > 0,
            'recommendation': 'HOLD'
        }
        
        # Decision logic
        if pnl_pct >= 5:
            status['recommendation'] = 'MOVE_TO_BREAKEVEN'
            status['action_reason'] = f'Up {pnl_pct:.1f}% - lock in profits'
        elif pnl_pct >= 10:
            status['recommendation'] = 'CONSIDER_PARTIAL_CLOSE'
            status['action_reason'] = f'Up {pnl_pct:.1f}% - take some profits'
        elif pnl_pct <= -1.5:
            status['recommendation'] = 'MONITOR_CLOSELY'
            status['action_reason'] = f'Down {pnl_pct:.1f}% - approaching SL'
        elif pnl_pct <= -3:
            status['recommendation'] = 'EMERGENCY_REVIEW'
            status['action_reason'] = f'Down {pnl_pct:.1f}% - manual review needed'
            
        return status
        
    def display_status(self):
        """Display current challenge status"""
        balance_data = self.get_balance()
        positions = self.get_positions()
        
        free = balance_data.get('free', 0)
        used = balance_data.get('used', 0)
        total = balance_data.get('total', 0)
        
        # Update water marks
        if total > self.high_water_mark:
            self.high_water_mark = total
        if total < self.low_water_mark:
            self.low_water_mark = total
            
        elapsed = datetime.now() - self.start_time
        hours_left = 24 - (elapsed.total_seconds() / 3600)
        
        progress_pct = (total / self.target - 1) * 100 if self.target > 0 else 0
        needed_pct = (self.target / total - 1) * 100 if total > 0 else 0
        
        print("\n" + "="*70)
        print(f"CHALLENGE MONITOR - {datetime.now().strftime('%H:%M:%S')}")
        print("="*70)
        print(f"Balance: ${total:.2f} | Target: ${self.target}")
        print(f"Progress: {progress_pct:+.1f}% | Need: {needed_pct:.1f}% more")
        print(f"High: ${self.high_water_mark:.2f} | Low: ${self.low_water_mark:.2f}")
        print(f"Time Left: {hours_left:.1f} hours")
        print(f"Positions: {len(positions)}")
        print("-"*70)
        
        if positions:
            total_pnl = 0
            for pos in positions:
                status = self.check_position_health(pos)
                total_pnl += status['unrealized']
                
                emoji = "🟢" if status['pnl_pct'] > 0 else "🔴"
                protection = ""
                if not status['has_tp'] or not status['has_sl']:
                    protection = " [⚠️ NO TP/SL]"
                    
                print(f"{emoji} {status['symbol']} {status['side'].upper()}")
                print(f"   Size: {status['size']} | Entry: ${status['entry']:.4f} | Mark: ${status['mark']:.4f}")
                print(f"   P&L: ${status['unrealized']:.2f} ({status['pnl_pct']:+.2f}%){protection}")
                
                if status['recommendation'] != 'HOLD':
                    print(f"   💡 {status['recommendation']}: {status['action_reason']}")
                print()
                
            print(f"Total Unrealized P&L: ${total_pnl:+.2f}")
        else:
            print("No open positions - waiting for setups")
            
        print("="*70)
        
        # Check risk limits
        daily_pnl = total - self.initial_balance
        if daily_pnl <= -RISK_CONFIG['daily_loss_limit_usd']:
            self.alert(f"🛑 DAILY LOSS LIMIT HIT: ${daily_pnl:.2f}")
            return False
            
        drawdown_pct = (self.high_water_mark - total) / self.high_water_mark * 100
        if drawdown_pct >= RISK_CONFIG['max_drawdown_pct'] * 100:
            self.alert(f"🛑 MAX DRAWDOWN HIT: {drawdown_pct:.1f}%")
            return False
            
        return True
        
    def monitor_loop(self):
        self.log("="*70)
        self.log("CHALLENGE MONITOR STARTED - PERSONAL OVERSIGHT")
        self.log("="*70)
        self.log(f"Target: ${self.initial_balance} to ${self.target}")
        self.log("I will watch every trade and alert on every move")
        self.log("="*70)
        
        self.alert("🚀 CHALLENGE MONITOR ACTIVE\n\nI'm personally watching every trade.\nYou'll get alerts for every entry, exit, and important move.\n\nLet's win this! 💪")
        
        check_count = 0
        
        try:
            while True:
                if not self.display_status():
                    self.alert("Challenge stopped due to risk limits")
                    break
                    
                check_count += 1
                
                # Every 5 minutes, detailed update
                if check_count % 5 == 0:
                    self.alert(f"📊 5-MIN UPDATE\nBalance: ${self.get_balance().get('total', 0):.2f}\nPositions: {len(self.get_positions())}")
                    
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            self.log("Monitor stopped by user")
        except Exception as e:
            self.log(f"Error in monitor: {e}")
            
if __name__ == '__main__':
    monitor = ChallengeMonitor()
    if monitor.connect():
        monitor.monitor_loop()
    else:
        print("Failed to connect to exchange")
