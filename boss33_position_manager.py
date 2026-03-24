"""
BOSS33 Position Manager - Trailing Stops & Breakeven
Monitors positions and adjusts stops as profits move
"""

import ccxt
import time
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('boss33_position_manager.log'),
        logging.StreamHandler()
    ]
)

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

class PositionManager:
    def __init__(self):
        self.exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'linear'}
        })
        self.trailing_activated = {}  # Track which positions have trailing stop
        
    def get_positions(self):
        """Get all open positions with full details"""
        positions = {}
        symbols = [
            'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT', 
            'DOGE/USDT:USDT', 'XRP/USDT:USDT', 'LINK/USDT:USDT', 'AVAX/USDT:USDT',
            'DOT/USDT:USDT', 'LTC/USDT:USDT', 'BCH/USDT:USDT'
        ]
        
        for symbol in symbols:
            try:
                pos_list = self.exchange.fetch_positions([symbol])
                if pos_list and len(pos_list) > 0:
                    pos = pos_list[0]
                    contracts = float(pos.get('contracts', 0))
                    if contracts > 0:
                        positions[symbol] = {
                            'side': pos['side'],
                            'entry': float(pos['entryPrice']),
                            'mark': float(pos['markPrice']),
                            'size': contracts,
                            'pnl': float(pos.get('unrealizedPnl', 0)),
                            'stop_loss': pos.get('stopLossPrice'),
                            'take_profit': pos.get('takeProfitPrice'),
                            'leverage': float(pos.get('leverage', 1))
                        }
            except Exception as e:
                logging.error(f"Error fetching {symbol}: {e}")
        return positions
    
    def calculate_pnl_pct(self, pos):
        """Calculate PnL percentage"""
        entry = pos['entry']
        mark = pos['mark']
        side = pos['side']
        
        if side == 'long':
            return ((mark - entry) / entry) * 100
        else:
            return ((entry - mark) / entry) * 100
    
    def set_trailing_stop(self, symbol, side, current_price, activation_pct=2.5, trail_pct=1.5):
        """Set trailing stop for a position"""
        try:
            # Get position size
            positions = self.exchange.fetch_positions([symbol])
            if not positions:
                return False
            
            pos = positions[0]
            size = float(pos['contracts'])
            
            if size == 0:
                return False
            
            # Calculate trailing stop price
            if side == 'long':
                trail_price = current_price * (1 - trail_pct/100)
                close_side = 'sell'
            else:
                trail_price = current_price * (1 + trail_pct/100)
                close_side = 'buy'
            
            # Set trailing stop order
            order = self.exchange.create_order(
                symbol=symbol,
                type='trailingStop',
                side=close_side,
                amount=size,
                price=None,
                params={
                    'triggerPrice': current_price,
                    'trailingStop': trail_pct,
                    'reduceOnly': True
                }
            )
            
            logging.info(f"✅ Trailing stop set for {symbol}: {trail_pct}% trail")
            return True
            
        except Exception as e:
            logging.error(f"Error setting trailing stop for {symbol}: {e}")
            return False
    
    def move_to_breakeven(self, symbol, side, entry_price, size):
        """Move stop loss to breakeven (+0.5% buffer)"""
        try:
            if side == 'long':
                breakeven = entry_price * 1.005
                close_side = 'sell'
            else:
                breakeven = entry_price * 0.995
                close_side = 'buy'
            
            # Create stop loss order at breakeven
            order = self.exchange.create_order(
                symbol=symbol,
                type='stopLoss',
                side=close_side,
                amount=size,
                price=None,
                params={
                    'stopLossPrice': breakeven,
                    'reduceOnly': True
                }
            )
            
            logging.info(f"🎯 Breakeven stop set for {symbol}: ${breakeven:.2f}")
            return True
            
        except Exception as e:
            logging.error(f"Error setting breakeven for {symbol}: {e}")
            return False
    
    def manage_positions(self):
        """Main position management loop"""
        positions = self.get_positions()
        
        if not positions:
            logging.info("No open positions to manage")
            return
        
        logging.info(f"\nManaging {len(positions)} positions...")
        
        for symbol, pos in positions.items():
            pnl_pct = self.calculate_pnl_pct(pos)
            side = pos['side']
            entry = pos['entry']
            mark = pos['mark']
            size = pos['size']
            
            logging.info(f"\n  {symbol}: {side.upper()} | Entry: ${entry:.2f} | Mark: ${mark:.2f} | PnL: {pnl_pct:+.2f}%")
            
            # Strategy levels
            BREAKEVEN_TRIGGER = 2.5  # Move to breakeven at +2.5%
            TRAILING_TRIGGER = 4.0   # Activate trailing at +4%
            
            pos_key = f"{symbol}_{side}"
            
            # Check if we should move to breakeven
            if pnl_pct >= BREAKEVEN_TRIGGER and pos_key not in self.trailing_activated:
                logging.info(f"    🎯 Profit > {BREAKEVEN_TRIGGER}% - Moving stop to breakeven")
                if self.move_to_breakeven(symbol, side, entry, size):
                    self.trailing_activated[pos_key] = 'breakeven'
            
            # Check if we should activate trailing stop
            elif pnl_pct >= TRAILING_TRIGGER and self.trailing_activated.get(pos_key) != 'trailing':
                logging.info(f"    🚀 Profit > {TRAILING_TRIGGER}% - Activating trailing stop")
                if self.set_trailing_stop(symbol, side, mark):
                    self.trailing_activated[pos_key] = 'trailing'
            
            # Show current status
            if pos_key in self.trailing_activated:
                status = self.trailing_activated[pos_key]
                logging.info(f"    Status: {status.upper()}")
            else:
                logging.info(f"    Status: NORMAL (SL at entry ±2%)")
    
    def run(self):
        """Main monitoring loop"""
        logging.info("="*60)
        logging.info("BOSS33 Position Manager - STARTED")
        logging.info("="*60)
        logging.info("Breakeven: +2.5% profit")
        logging.info("Trailing Stop: +4% profit")
        logging.info("="*60)
        
        try:
            while True:
                self.manage_positions()
                logging.info("\n" + "-"*40)
                time.sleep(30)  # Check every 30 seconds
        except KeyboardInterrupt:
            logging.info("\nPosition Manager stopped")

if __name__ == '__main__':
    manager = PositionManager()
    manager.run()
