"""
Auto-cleanup orphaned orders - runs continuously to remove limit/conditional orders
that don't have corresponding open positions
"""

import ccxt
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('orphan_cleanup.log'),
        logging.StreamHandler()
    ]
)

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

# All trading pairs to monitor
SYMBOLS = [
    'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT',
    'DOGE/USDT:USDT', 'XRP/USDT:USDT', 'LINK/USDT:USDT', 'AVAX/USDT:USDT',
    'DOT/USDT:USDT', 'LTC/USDT:USDT', 'BCH/USDT:USDT', 'UNI/USDT:USDT',
    'ATOM/USDT:USDT', 'ETC/USDT:USDT', 'ARB/USDT:USDT', 'OP/USDT:USDT',
    'NEAR/USDT:USDT', 'APT/USDT:USDT', 'SUI/USDT:USDT', 'MATIC/USDT:USDT'
]

class OrphanOrderCleaner:
    def __init__(self):
        self.exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'linear'}
        })
        
    def get_position_size(self, symbol):
        """Check if position exists for symbol"""
        try:
            positions = self.exchange.fetch_positions([symbol])
            if positions and len(positions) > 0:
                return float(positions[0].get('contracts', 0))
        except:
            pass
        return 0
    
    def cleanup_symbol(self, symbol):
        """Clean up orders for a symbol with no position"""
        try:
            # Check position
            position_size = self.get_position_size(symbol)
            
            if position_size > 0:
                # Position exists - leave orders alone
                return 0
            
            # No position - check for orphaned orders
            orders = self.exchange.fetch_open_orders(symbol)
            
            if not orders:
                return 0
            
            # Found orphaned orders - cancel them all
            cancelled_count = 0
            for order in orders:
                try:
                    self.exchange.cancel_order(order['id'], symbol)
                    cancelled_count += 1
                except:
                    pass
            
            if cancelled_count > 0:
                logging.info(f"CANCELLED {cancelled_count} orphaned orders for {symbol}")
            
            return cancelled_count
            
        except Exception as e:
            logging.debug(f"Error checking {symbol}: {e}")
            return 0
    
    def run_cleanup(self):
        """Run one cleanup cycle"""
        total_cancelled = 0
        
        for symbol in SYMBOLS:
            count = self.cleanup_symbol(symbol)
            total_cancelled += count
            time.sleep(0.5)  # Rate limit
        
        return total_cancelled
    
    def run_continuous(self):
        """Run continuous cleanup every 30 seconds"""
        logging.info("=" * 60)
        logging.info("ORPHAN ORDER CLEANUP STARTED")
        logging.info("Checking every 30 seconds for orphaned orders")
        logging.info("=" * 60)
        
        try:
            while True:
                cancelled = self.run_cleanup()
                
                if cancelled > 0:
                    logging.info(f"TOTAL CANCELLED THIS CYCLE: {cancelled}")
                
                logging.debug("Cleanup cycle complete. Sleeping 30s...")
                time.sleep(30)
                
        except KeyboardInterrupt:
            logging.info("Cleanup stopped by user")

if __name__ == '__main__':
    cleaner = OrphanOrderCleaner()
    cleaner.run_continuous()
