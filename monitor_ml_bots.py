"""
ML Trading Bot Monitor & Launcher
Starts and monitors all ML trading bots
"""

import subprocess
import sys
import os
import time
import json
import logging
from datetime import datetime
import threading
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ml_trading_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('MLMonitor')

class MLBotMonitor:
    def __init__(self):
        self.symbols = [
            'ETH/USDT:USDT',
            'NEAR/USDT:USDT', 
            'DOGE/USDT:USDT'
        ]
        self.processes = {}
        self.running = True
        self.performance_data = {}
        
    def start_bot(self, symbol):
        """Start a single ML trading bot"""
        safe_symbol = symbol.replace('/', '_')
        log_file = f'ml_bot_{safe_symbol}.log'
        
        try:
            # Start bot in background
            process = subprocess.Popen(
                [sys.executable, 'ml_trader_live.py', '--symbol', symbol],
                stdout=open(log_file, 'a'),
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            self.processes[symbol] = {
                'process': process,
                'pid': process.pid,
                'start_time': datetime.now(),
                'log_file': log_file,
                'status': 'running'
            }
            
            logger.info(f"Started {symbol} bot (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start {symbol}: {e}")
            return False
    
    def start_all_bots(self):
        """Start all ML trading bots"""
        logger.info("="*60)
        logger.info("STARTING ALL ML TRADING BOTS")
        logger.info("="*60)
        
        for symbol in self.symbols:
            self.start_bot(symbol)
            time.sleep(2)  # Stagger starts
        
        logger.info(f"\nStarted {len(self.processes)} bots")
        self.save_status()
    
    def check_bot_health(self):
        """Check if all bots are running"""
        for symbol, info in self.processes.items():
            process = info['process']
            
            # Check if process is alive
            if process.poll() is not None:
                logger.warning(f"{symbol} bot crashed! Restarting...")
                self.start_bot(symbol)
            else:
                info['status'] = 'running'
        
        self.save_status()
    
    def monitor_loop(self):
        """Main monitoring loop"""
        logger.info("\nMonitor active. Press Ctrl+C to stop all bots.\n")
        
        while self.running:
            try:
                self.check_bot_health()
                self.log_summary()
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                logger.info("\nStopping all bots...")
                self.stop_all()
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(30)
    
    def log_summary(self):
        """Log current status summary"""
        running = sum(1 for info in self.processes.values() if info['status'] == 'running')
        logger.info(f"Status: {running}/{len(self.symbols)} bots running")
    
    def save_status(self):
        """Save current status to file"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'bots': {
                symbol: {
                    'pid': info['pid'],
                    'status': info['status'],
                    'start_time': info['start_time'].isoformat(),
                    'log_file': info['log_file']
                }
                for symbol, info in self.processes.items()
            }
        }
        
        with open('ml_trading_status.json', 'w') as f:
            json.dump(status, f, indent=2)
    
    def stop_all(self):
        """Stop all bots"""
        logger.info("Stopping all ML trading bots...")
        
        for symbol, info in self.processes.items():
            try:
                process = info['process']
                process.terminate()
                process.wait(timeout=5)
                logger.info(f"Stopped {symbol}")
            except:
                try:
                    process.kill()
                except:
                    pass
        
        self.running = False
        logger.info("All bots stopped")
    
    def run(self):
        """Main entry point"""
        self.start_all_bots()
        
        try:
            self.monitor_loop()
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            self.stop_all()

if __name__ == "__main__":
    monitor = MLBotMonitor()
    monitor.run()
