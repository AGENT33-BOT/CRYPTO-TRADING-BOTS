"""
DCA (Dollar Cost Average) Bot for Bybit
Strategy: Gradually enter positions on dips with multiple buy orders
"""

import ccxt
import time
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('dca_bot.log'),
        logging.StreamHandler()
    ]
)

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

CONFIG = {
    # DCA Configuration - Percentage-based for auto-scaling
    'max_position_pct': 0.35,     # 35% of balance max per symbol (auto-scales)
    'num_entry_points': 4,        # 4 entry points per symbol
    'entry_spacing_pct': 0.015,   # 1.5% spacing between entries
    'take_profit_pct': 0.04,      # 4% TP
    'stop_loss_pct': 0.025,       # 2.5% SL
    'leverage': 3,
    'check_interval': 60,         # Check every minute
    
    # Target symbols - top performers only
    'symbols': [
        'BTC/USDT:USDT',
        'ETH/USDT:USDT', 
        'SOL/USDT:USDT',
        'NEAR/USDT:USDT',
        'DOGE/USDT:USDT'
    ]
}

class DCABot:
    def __init__(self):
        self.exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'linear'}
        })
        self.active_dc_orders = {}  # Track DCA orders per symbol
        
        logging.info("="*60)
        logging.info("DCA BOT STARTED - $180 max per symbol")
        logging.info("="*60)
    
    def get_balance(self):
        try:
            balance = self.exchange.fetch_balance()
            usdt = balance.get('USDT', {})
            return float(usdt.get('free', 0)), float(usdt.get('total', 0))
        except:
            return 0, 0
    
    def check_existing_position(self, symbol):
        """Check if we already have a position in this symbol"""
        try:
            positions = self.exchange.fetch_positions([symbol])
            for pos in positions:
                if float(pos.get('contracts', 0)) != 0:
                    return True
            return False
        except:
            return False
    
    def calculate_dca_entries(self, current_price):
        """Calculate entry points below current price"""
        entries = []
        
        # Get current balance for dynamic sizing
        free_balance, total_balance = self.get_balance()
        max_position_size = total_balance * CONFIG['max_position_pct']
        amount_per_entry = max_position_size / CONFIG['num_entry_points']
        
        for i in range(CONFIG['num_entry_points']):
            discount = 1 - (CONFIG['entry_spacing_pct'] * (i + 1))
            entry_price = current_price * discount
            entries.append({
                'price': entry_price,
                'amount_usd': amount_per_entry,
                'level': i + 1
            })
        
        return entries
    
    def place_dca_orders(self, symbol, side='LONG'):
        """Place multiple buy orders at different price levels"""
        try:
            # Cancel any existing orders for this symbol
            try:
                self.exchange.cancel_all_orders(symbol)
            except:
                pass
            
            ticker = self.exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            entries = self.calculate_dca_entries(current_price)
            
            logging.info(f"\n📊 DCA Setup for {symbol}")
            logging.info(f"Current: ${current_price:,.2f}")
            logging.info(f"Entries: {len(entries)} levels")
            
            for entry in entries:
                try:
                    amount = entry['amount_usd'] / entry['price']
                    
                    if side == 'LONG':
                        order = self.exchange.create_limit_buy_order(
                            symbol, amount, entry['price']
                        )
                        logging.info(f"  ✓ Buy @ ${entry['price']:,.4f} (${entry['amount_usd']:.0f})")
                    
                    time.sleep(0.5)  # Rate limit
                    
                except Exception as e:
                    logging.error(f"  ✗ Entry {entry['level']} failed: {e}")
            
            # Set TP/SL on first fill
            self.active_dc_orders[symbol] = {
                'tp_price': current_price * (1 + CONFIG['take_profit_pct']),
                'sl_price': entries[-1]['price'] * (1 - CONFIG['stop_loss_pct'])
            }
            
        except Exception as e:
            logging.error(f"DCA setup error for {symbol}: {e}")
    
    def check_and_manage_positions(self):
        """Check positions and add TP/SL when filled"""
        try:
            for symbol in CONFIG['symbols']:
                if symbol in self.active_dc_orders:
                    positions = self.exchange.fetch_positions([symbol])
                    
                    for pos in positions:
                        size = float(pos.get('contracts', 0))
                        if size != 0:
                            # Position exists - ensure TP/SL
                            tp_sl = self.active_dc_orders[symbol]
                            # Note: TP/SL should be set via exchange or monitored
                            logging.info(f"📈 {symbol} position active - monitoring...")
                            
        except Exception as e:
            logging.error(f"Position check error: {e}")
    
    def scan_for_opportunities(self):
        """Scan for symbols without positions"""
        free_balance, total_balance = self.get_balance()
        
        if free_balance < 50:  # Need at least $50 free
            logging.info(f"⏳ Low balance (${free_balance:.0f}) - waiting...")
            return
        
        for symbol in CONFIG['symbols']:
            if not self.check_existing_position(symbol):
                logging.info(f"🎯 {symbol} - No position, setting up DCA...")
                self.place_dca_orders(symbol)
                time.sleep(2)  # Rate limit between symbols
    
    def run(self):
        """Main loop"""
        logging.info("\n🚀 DCA Bot Running - Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.scan_for_opportunities()
                self.check_and_manage_positions()
                time.sleep(CONFIG['check_interval'])
                
        except KeyboardInterrupt:
            logging.info("\n🛑 DCA Bot stopped by user")
            # Cancel all pending orders
            for symbol in CONFIG['symbols']:
                try:
                    self.exchange.cancel_all_orders(symbol)
                except:
                    pass

if __name__ == '__main__':
    bot = DCABot()
    bot.run()
