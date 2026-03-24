"""
Continuous Learning System for ML Trading Bots
Automatically retrains models with new data to adapt to market changes
"""

import schedule
import time
import os
import json
from datetime import datetime, timedelta
import threading
import subprocess
import sys

class ContinuousLearningSystem:
    def __init__(self):
        self.symbols = [
            ('ETH/USDT:USDT', '15m'),
            ('NEAR/USDT:USDT', '15m'),
            ('DOGE/USDT:USDT', '15m')
        ]
        self.performance_log = 'ml_performance.json'
        self.last_retrain = {}
        self.learning_active = True
        
    def log_trade_outcome(self, symbol, action, entry_price, exit_price, pnl, confidence):
        """Log every trade outcome for learning"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'action': action,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'confidence': confidence,
            'was_correct': pnl > 0
        }
        
        # Append to performance log
        try:
            if os.path.exists(self.performance_log):
                with open(self.performance_log, 'r') as f:
                    data = json.load(f)
            else:
                data = {'trades': [], 'daily_stats': {}}
            
            data['trades'].append(log_entry)
            
            # Keep only last 1000 trades
            if len(data['trades']) > 1000:
                data['trades'] = data['trades'][-1000:]
            
            with open(self.performance_log, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error logging trade: {e}")
    
    def calculate_performance_metrics(self, symbol=None, days=7):
        """Calculate recent performance metrics"""
        try:
            if not os.path.exists(self.performance_log):
                return None
            
            with open(self.performance_log, 'r') as f:
                data = json.load(f)
            
            trades = data.get('trades', [])
            
            # Filter by symbol if specified
            if symbol:
                trades = [t for t in trades if t['symbol'] == symbol]
            
            # Filter by date
            cutoff = datetime.now() - timedelta(days=days)
            recent_trades = [t for t in trades if datetime.fromisoformat(t['timestamp']) > cutoff]
            
            if not recent_trades:
                return None
            
            total_trades = len(recent_trades)
            winning_trades = sum(1 for t in recent_trades if t['was_correct'])
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            total_pnl = sum(t['pnl'] for t in recent_trades)
            avg_confidence = sum(t['confidence'] for t in recent_trades) / total_trades
            
            return {
                'total_trades': total_trades,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'avg_confidence': avg_confidence,
                'needs_retrain': win_rate < 0.55 or total_trades < 5  # Retrain if <55% win rate
            }
            
        except Exception as e:
            print(f"Error calculating metrics: {e}")
            return None
    
    def retrain_model(self, symbol, timeframe):
        """Retrain a single model with fresh data"""
        print(f"\n{'='*60}")
        print(f"RETRAINING: {symbol}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        try:
            # Run training script
            result = subprocess.run(
                [sys.executable, 'train_lightweight.py'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                print(f"✓ {symbol} retrained successfully!")
                self.last_retrain[symbol] = datetime.now().isoformat()
                
                # Send Telegram notification
                self._send_retrain_notification(symbol, "success")
                return True
            else:
                print(f"✗ {symbol} retraining failed:")
                print(result.stderr)
                self._send_retrain_notification(symbol, "failed", result.stderr)
                return False
                
        except Exception as e:
            print(f"✗ Error retraining {symbol}: {e}")
            return False
    
    def _send_retrain_notification(self, symbol, status, error=None):
        """Send Telegram notification about retraining"""
        try:
            from telegram_reporter import TelegramReporter
            
            BOT_TOKEN = "8586893914:AAEIuNFlGNbhDeUQ-eXUOmTm0KHw_-aOtuI"
            CHAT_ID = "5804173449"
            
            reporter = TelegramReporter(BOT_TOKEN, chat_id=CHAT_ID)
            
            if status == "success":
                message = f"""
🧠 <b>ML MODEL RETRAINED</b> 🧠

📊 Symbol: <b>{symbol}</b>
✅ Status: <b>Success</b>
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Model updated with latest market data!
Ready for improved predictions.
"""
            else:
                message = f"""
⚠️ <b>ML RETRAIN WARNING</b> ⚠️

📊 Symbol: <b>{symbol}</b>
❌ Status: <b>Failed</b>
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Using previous model.
"""
            
            reporter.send_message(message)
            
        except Exception as e:
            print(f"Could not send notification: {e}")
    
    def check_and_retrain(self):
        """Check performance and retrain if needed"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checking performance...")
        
        for symbol, timeframe in self.symbols:
            metrics = self.calculate_performance_metrics(symbol)
            
            if metrics:
                print(f"\n{symbol}:")
                print(f"  Trades: {metrics['total_trades']}")
                print(f"  Win Rate: {metrics['win_rate']:.1%}")
                print(f"  P&L: ${metrics['total_pnl']:.2f}")
                
                if metrics['needs_retrain']:
                    print(f"  ⚠️ Performance below threshold. Retraining...")
                    self.retrain_model(symbol, timeframe)
                else:
                    print(f"  ✓ Performance good. No retrain needed.")
            else:
                print(f"{symbol}: No recent trade data")
    
    def scheduled_retrain(self):
        """Scheduled retrain - runs daily at 00:00"""
        print(f"\n{'='*60}")
        print(f"SCHEDULED DAILY RETRAIN")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        for symbol, timeframe in self.symbols:
            self.retrain_model(symbol, timeframe)
            time.sleep(5)  # Brief pause between models
    
    def adaptive_learning_check(self):
        """Check if market regime changed significantly"""
        # This would analyze recent data for regime shifts
        # For now, just log that check happened
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Adaptive check completed")
    
    def start_continuous_learning(self):
        """Start the continuous learning loop"""
        print("="*60)
        print("CONTINUOUS LEARNING SYSTEM STARTED")
        print("="*60)
        print("\nSchedule:")
        print("  - Performance check: Every 4 hours")
        print("  - Retrain if needed: Automatic")
        print("  - Full retrain: Daily at 00:00")
        print("  - Adaptive check: Every 6 hours")
        print("="*60)
        
        # Schedule jobs
        schedule.every(4).hours.do(self.check_and_retrain)
        schedule.every().day.at("00:00").do(self.scheduled_retrain)
        schedule.every(6).hours.do(self.adaptive_learning_check)
        
        # Run initial check
        self.check_and_retrain()
        
        # Keep running
        while self.learning_active:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop(self):
        """Stop continuous learning"""
        self.learning_active = False
        print("Continuous learning stopped")


if __name__ == "__main__":
    # Start continuous learning
    learning_system = ContinuousLearningSystem()
    
    try:
        learning_system.start_continuous_learning()
    except KeyboardInterrupt:
        print("\nStopping...")
        learning_system.stop()
