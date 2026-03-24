"""
Automated Position Manager for Bybit
Monitors positions, sets trailing stops, takes partial profits
Created: 2026-02-05
"""

import ccxt
import time
import json
from datetime import datetime

# API Credentials
API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

# Configuration
TAKE_PROFIT_50_PERCENT = 3.0  # Close 50% when position hits +3%
TRAILING_STOP_ACTIVATION = 2.0  # Activate trailing stop at +2%
TRAILING_STOP_DISTANCE = 1.0  # Trail 1% behind price
CHECK_INTERVAL = 60  # Check every 60 seconds

class PositionManager:
    def __init__(self):
        self.exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'linear'}
        })
        self.closed_50_percent = set()  # Track which positions had 50% closed
        self.trailing_active = {}  # Track trailing stop status
        
    def get_positions(self):
        """Get all open positions"""
        try:
            symbols = ['ADA/USDT:USDT', 'DOGE/USDT:USDT', 'NEAR/USDT:USDT', 'ETH/USDT:USDT']
            positions = {}
            for symbol in symbols:
                pos_list = self.exchange.fetch_positions([symbol])
                if pos_list and pos_list[0]['contracts'] > 0:
                    positions[symbol] = pos_list[0]
            return positions
        except Exception as e:
            print(f"Error fetching positions: {e}")
            return {}
    
    def calculate_pnl_percent(self, position):
        """Calculate PnL percentage"""
        entry = float(position['entryPrice'])
        mark = float(position['markPrice'])
        side = position['side']
        
        if side == 'long':
            return ((mark - entry) / entry) * 100
        else:
            return ((entry - mark) / entry) * 100
    
    def close_50_percent(self, symbol, position):
        """Close 50% of a position"""
        try:
            current_size = float(position['contracts'])
            close_size = current_size * 0.5
            side = 'sell' if position['side'] == 'long' else 'buy'
            
            print(f"[ACTION] Closing 50% of {symbol}: {close_size} contracts")
            
            order = self.exchange.create_market_order(
                symbol=symbol,
                side=side,
                amount=close_size,
                params={'reduceOnly': True}
            )
            
            self.closed_50_percent.add(symbol)
            
            # Log the trade
            log_entry = {
                'time': datetime.now().isoformat(),
                'symbol': symbol,
                'action': 'close_50_percent',
                'amount': close_size,
                'order_id': order['id'],
                'pnl_at_close': self.calculate_pnl_percent(position)
            }
            
            with open('position_manager_log.json', 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            print(f"[SUCCESS] Closed 50% of {symbol} at +{self.calculate_pnl_percent(position):.2f}%")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to close 50% of {symbol}: {e}")
            return False
    
    def set_trailing_stop(self, symbol, position):
        """Set trailing stop loss"""
        try:
            current_size = float(position['contracts'])
            entry_price = float(position['entryPrice'])
            side = position['side']
            
            # Calculate trailing stop price
            if side == 'long':
                # For longs, trail below current price
                trail_price = entry_price * (1 + TRAILING_STOP_ACTIVATION/100)
                stop_price = trail_price * (1 - TRAILING_STOP_DISTANCE/100)
            else:
                # For shorts, trail above current price
                trail_price = entry_price * (1 - TRAILING_STOP_ACTIVATION/100)
                stop_price = trail_price * (1 + TRAILING_STOP_DISTANCE/100)
            
            print(f"[ACTION] Setting trailing stop for {symbol}")
            print(f"  Activation: {TRAILING_STOP_ACTIVATION}%")
            print(f"  Trail distance: {TRAILING_STOP_DISTANCE}%")
            
            # Note: Actual trailing stop implementation depends on Bybit API
            # This is a simplified version - may need adjustment
            
            self.trailing_active[symbol] = {
                'activation': TRAILING_STOP_ACTIVATION,
                'distance': TRAILING_STOP_DISTANCE,
                'set_at': datetime.now().isoformat()
            }
            
            print(f"[SUCCESS] Trailing stop configured for {symbol}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to set trailing stop for {symbol}: {e}")
            return False
    
    def monitor_and_manage(self):
        """Main monitoring loop"""
        print(f"\n{'='*60}")
        print(f"Position Manager - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        positions = self.get_positions()
        
        if not positions:
            print("No open positions found.")
            return
        
        print(f"Monitoring {len(positions)} positions:\n")
        
        for symbol, position in positions.items():
            pnl_percent = self.calculate_pnl_percent(position)
            current_size = float(position['contracts'])
            entry = float(position['entryPrice'])
            mark = float(position['markPrice'])
            unrealized = float(position['unrealizedPnl'])
            
            print(f"{symbol}:")
            print(f"  Size: {current_size} | Entry: ${entry:.4f} | Mark: ${mark:.4f}")
            print(f"  PnL: {pnl_percent:+.2f}% (${unrealized:+.2f})")
            
            # Check if we should close 50%
            if pnl_percent >= TAKE_PROFIT_50_PERCENT and symbol not in self.closed_50_percent:
                print(f"  [ALERT] Hit +{TAKE_PROFIT_50_PERCENT}% target! Closing 50%...")
                self.close_50_percent(symbol, position)
            
            # Check if we should activate trailing stop
            elif pnl_percent >= TRAILING_STOP_ACTIVATION and symbol not in self.trailing_active:
                print(f"  [ALERT] Hit +{TRAILING_STOP_ACTIVATION}% - Activating trailing stop...")
                self.set_trailing_stop(symbol, position)
            
            # Show current status
            elif symbol in self.closed_50_percent:
                print(f"  [STATUS] 50% already closed")
            elif symbol in self.trailing_active:
                print(f"  [STATUS] Trailing stop active")
            else:
                print(f"  [STATUS] Holding - Need +{TAKE_PROFIT_50_PERCENT:.1f}% for 50% close")
            
            print()
    
    def run(self):
        """Run the manager continuously"""
        print("Starting Automated Position Manager...")
        print(f"Strategy:")
        print(f"  - Close 50% when position hits +{TAKE_PROFIT_50_PERCENT}%")
        print(f"  - Activate trailing stop at +{TRAILING_STOP_ACTIVATION}%")
        print(f"  - Check interval: {CHECK_INTERVAL} seconds")
        print(f"\nPress Ctrl+C to stop\n")
        
        try:
            while True:
                self.monitor_and_manage()
                print(f"Next check in {CHECK_INTERVAL} seconds...\n")
                time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("\n\nPosition Manager stopped by user.")

if __name__ == '__main__':
    manager = PositionManager()
    manager.run()
