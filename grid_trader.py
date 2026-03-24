"""
Grid Trading Bot for Bybit
Strategy: Place buy/sell orders at set intervals within a price range
Profits from volatility in sideways markets
"""

import ccxt
import time
import logging
from datetime import datetime
import sys
import os
import atexit

# File lock to prevent multiple instances (Windows compatible)
LOCK_FILE = 'grid_trader.lock'
lock_handle = None

# POSITION SIZING RULES - From analysis Feb 23, 2026
POSITION_CONFIG = {
    'max_position_pct': 0.15,    # Max 15% of account per position
    'max_symbol_pct': 0.25,      # Max 25% per symbol  
    'min_free_balance': 5,       # Minimum $5 free balance required (REDUCED from 15)
    'max_total_investment_pct': 0.50,  # Max 50% of account in grid
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('grid_trading.log'),
        logging.StreamHandler()
    ]
)

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

def acquire_lock():
    """Acquire file lock to prevent multiple instances"""
    global lock_handle
    try:
        if os.path.exists(LOCK_FILE):
            # Check if process is actually running
            try:
                with open(LOCK_FILE, 'r') as f:
                    old_pid = f.read().strip()
                    if old_pid:
                        # Check if process exists (Windows)
                        import subprocess
                        result = subprocess.run(['tasklist', '/FI', f'PID eq {old_pid}'], 
                                              capture_output=True, text=True)
                        if old_pid in result.stdout:
                            logging.error(f"Another grid trader instance is running (PID: {old_pid})")
                            return False
            except:
                pass
            # Stale lock file, remove it
            try:
                os.remove(LOCK_FILE)
            except:
                pass
        
        # Create new lock file
        lock_handle = open(LOCK_FILE, 'w')
        lock_handle.write(str(os.getpid()))
        lock_handle.flush()
        
        # Register cleanup on exit
        atexit.register(release_lock)
        return True
        
    except Exception as e:
        logging.error(f"Failed to acquire lock: {e}")
        return False

def release_lock():
    """Release file lock"""
    global lock_handle
    try:
        if lock_handle:
            lock_handle.close()
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except:
        pass

CONFIG = {
    'symbol': 'DOGE/USDT:USDT',  # Primary trading pair - DOGE
    'grid_levels': 10,           # Number of grid lines
    'grid_lower': 0.0910,        # Lower price bound (~2.5% below current $0.0933)
    'grid_upper': 0.0980,        # Upper price bound (~5% above current)
    'total_investment_pct': 0.20, # 20% of total balance for grid (auto-scales)
    'leverage': 2,
    'margin_mode': 'ISOLATED',
    'check_interval': 30,        # Check every 30 seconds
}

class GridTrader:
    def __init__(self):
        self.exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'},
            'urls': {
                'api': {
                    'public': 'https://api.bytick.com',
                    'private': 'https://api.bytick.com',
                }
            }
        })
        self.exchange.load_markets()
        self.active_orders = []
        self.grid_prices = []
        self.position_size_per_grid = 0
        
    def validate_position_sizing(self):
        """Validate grid investment against risk rules"""
        try:
            balance = self.get_balance()
            
            # Get total account balance
            total_balance_data = self.exchange.fetch_balance()
            total_balance = float(total_balance_data.get('USDT', {}).get('total', balance))
            
            # Check minimum free balance
            if balance < POSITION_CONFIG['min_free_balance']:
                logging.error(f"[RISK] Insufficient free balance: ${balance:.2f} (need ${POSITION_CONFIG['min_free_balance']})")
                return False
            
            # Calculate investment from percentage of balance
            calculated_investment = total_balance * CONFIG['total_investment_pct']
            
            # Check max total investment (50% of account)
            max_investment = total_balance * POSITION_CONFIG['max_total_investment_pct']
            if calculated_investment > max_investment:
                CONFIG['total_investment'] = max_investment
                logging.warning(f"[RISK] Grid investment reduced to ${max_investment:.2f} (50% limit)")
            else:
                CONFIG['total_investment'] = calculated_investment
            
            # Check if symbol would exceed 25% allocation
            symbol_allocation = CONFIG['total_investment_pct']
            if symbol_allocation > POSITION_CONFIG['max_symbol_pct']:
                logging.error(f"[RISK] Grid would use {symbol_allocation:.1%} of account (max 25%)")
                return False
            
            logging.info(f"[RISK] Position sizing validated: ${CONFIG['total_investment']:.2f} grid on ${total_balance:.2f} account")
            return True
            
        except Exception as e:
            logging.error(f"[RISK] Sizing validation error: {e}")
            return False
    
    def calculate_grid(self):
        """Calculate grid price levels with sizing validation"""
        # Validate position sizing first
        if not self.validate_position_sizing():
            logging.error("Grid calculation aborted - risk limits exceeded")
            sys.exit(1)
        
        lower = CONFIG['grid_lower']
        upper = CONFIG['grid_upper']
        levels = CONFIG['grid_levels']
        
        step = (upper - lower) / (levels - 1)
        self.grid_prices = [lower + (step * i) for i in range(levels)]
        
        # Calculate position size per grid
        self.position_size_per_grid = CONFIG['total_investment'] / levels
        
        logging.info(f"Grid set: {levels} levels from ${lower:,.4f} to ${upper:,.4f}")
        logging.info(f"Step size: ${step:,.4f} | Position per grid: ${self.position_size_per_grid:.2f}")
        
    def setup_leverage(self):
        """Set leverage and margin mode"""
        try:
            symbol = CONFIG['symbol']
            self.exchange.set_leverage(CONFIG['leverage'], symbol)
            logging.info(f"Leverage set to {CONFIG['leverage']}x")
        except Exception as e:
            logging.warning(f"Leverage setup: {e}")
            
    def get_current_price(self):
        """Get current mark price"""
        try:
            ticker = self.exchange.fetch_ticker(CONFIG['symbol'])
            return ticker['last']
        except Exception as e:
            logging.error(f"Price fetch error: {e}")
            return None
    
    def place_grid_orders(self):
        """Place initial grid orders"""
        current_price = self.get_current_price()
        if not current_price:
            return
        
        logging.info(f"Current price: ${current_price:,.2f}")
        
        # Cancel existing orders first
        try:
            self.exchange.cancel_all_orders(CONFIG['symbol'])
            logging.info("Cancelled existing orders")
        except:
            pass
        
        # Place buy orders below current price
        for price in self.grid_prices:
            if price < current_price:
                try:
                    amount = self.position_size_per_grid / price
                    order = self.exchange.create_limit_buy_order(
                        CONFIG['symbol'],
                        amount,
                        price
                    )
                    logging.info(f"BUY order placed: {amount:.6f} @ ${price:,.2f}")
                except Exception as e:
                    logging.error(f"Buy order error @ ${price}: {e}")
        
        # Place sell orders above current price
        for price in self.grid_prices:
            if price > current_price:
                try:
                    amount = self.position_size_per_grid / price
                    order = self.exchange.create_limit_sell_order(
                        CONFIG['symbol'],
                        amount,
                        price
                    )
                    logging.info(f"SELL order placed: {amount:.6f} @ ${price:,.2f}")
                except Exception as e:
                    logging.error(f"Sell order error @ ${price}: {e}")
    
    def check_filled_orders(self):
        """Check for filled orders and replace them"""
        try:
            orders = self.exchange.fetch_open_orders(CONFIG['symbol'])
            
            # If we have fewer orders than expected, some filled
            expected_orders = len(self.grid_prices) - 1  # Exclude current price level
            
            if len(orders) < expected_orders:
                logging.info(f"Orders filled! Replacing grid... ({len(orders)}/{expected_orders} remaining)")
                self.place_grid_orders()
                
        except Exception as e:
            logging.error(f"Order check error: {e}")
    
    def get_balance(self):
        """Get account balance"""
        try:
            balance = self.exchange.fetch_balance()
            usdt = balance.get('USDT', {})
            return float(usdt.get('free', 0))
        except:
            return 0
    
    def run(self):
        """Main loop"""
        logging.info("=" * 60)
        logging.info("GRID TRADING BOT STARTED")
        logging.info("=" * 60)
        
        self.calculate_grid()
        self.setup_leverage()
        
        balance = self.get_balance()
        logging.info(f"Available balance: ${balance:.2f} USDT")
        
        # Place initial grid
        self.place_grid_orders()
        
        logging.info("\nGrid active. Monitoring for fills...")
        logging.info("Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.check_filled_orders()
                time.sleep(CONFIG['check_interval'])
                
        except KeyboardInterrupt:
            logging.info("\nStopping grid bot...")
            try:
                self.exchange.cancel_all_orders(CONFIG['symbol'])
                logging.info("All orders cancelled")
            except:
                pass
            logging.info("Grid bot stopped")

if __name__ == '__main__':
    # Acquire lock to prevent multiple instances
    if not acquire_lock():
        print("ERROR: Another Grid Trader instance is already running!")
        print("Check task manager or wait for it to finish.")
        sys.exit(1)
    
    try:
        trader = GridTrader()
        trader.run()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        raise
    finally:
        release_lock()
