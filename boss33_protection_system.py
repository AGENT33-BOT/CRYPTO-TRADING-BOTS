"""
BOSS33 Auto Protection System
Ensures ALL positions have TP/SL set automatically
Runs continuously alongside main trading bot
"""

import ccxt
import time
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('boss33_protection.log'),
        logging.StreamHandler()
    ]
)

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

# Default protection settings
PROTECTION = {
    'stop_loss_pct': 2.0,      # 2% stop loss
    'take_profit_pct': 4.0,     # 4% take profit
    'trailing_stop_pct': 1.5,   # 1.5% trailing stop
}

class ProtectionManager:
    def __init__(self):
        self.exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'linear'}
        })
        self.protected_positions = {}  # Track which positions we've protected
        
    def get_all_positions(self):
        """Get all open positions across all symbols"""
        positions = {}
        symbols = [
            'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT', 
            'DOGE/USDT:USDT', 'XRP/USDT:USDT', 'LINK/USDT:USDT', 'AVAX/USDT:USDT',
            'DOT/USDT:USDT', 'LTC/USDT:USDT', 'BCH/USDT:USDT', 'UNI/USDT:USDT',
            'ATOM/USDT:USDT', 'ETC/USDT:USDT', 'ARB/USDT:USDT', 'OP/USDT:USDT',
            'NEAR/USDT:USDT', 'APT/USDT:USDT', 'SUI/USDT:USDT'
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
                logging.debug(f"Error fetching {symbol}: {e}")
        
        return positions
    
    def set_protection(self, symbol, pos):
        """Set TP/SL for a position"""
        try:
            side = pos['side']
            entry = pos['entry']
            size = pos['size']
            
            # Calculate TP/SL levels
            sl_pct = PROTECTION['stop_loss_pct'] / 100
            tp_pct = PROTECTION['take_profit_pct'] / 100
            
            if side == 'long':
                stop_loss = entry * (1 - sl_pct)
                take_profit = entry * (1 + tp_pct)
                close_side = 'sell'
            else:  # short
                stop_loss = entry * (1 + sl_pct)
                take_profit = entry * (1 - tp_pct)
                close_side = 'buy'
            
            # Cancel any existing TP/SL orders first
            try:
                self.exchange.cancel_all_orders(symbol)
                time.sleep(0.5)
            except:
                pass
            
            # Set Take Profit (limit order)
            try:
                tp_order = self.exchange.create_order(
                    symbol=symbol,
                    type='limit',
                    side=close_side,
                    amount=size,
                    price=round(take_profit, 4),
                    params={'reduceOnly': True}
                )
                logging.info(f"  [OK] TP set: ${take_profit:.4f}")
            except Exception as e:
                logging.error(f"  [ERROR] TP failed: {e}")
            
            # Set Stop Loss (conditional market order with trigger)
            try:
                trigger_dir = 'descending' if side == 'long' else 'ascending'
                sl_order = self.exchange.create_order(
                    symbol=symbol,
                    type='market',
                    side=close_side,
                    amount=size,
                    price=None,
                    params={
                        'triggerPrice': round(stop_loss, 4),
                        'triggerDirection': trigger_dir,
                        'reduceOnly': True
                    }
                )
                logging.info(f"  [OK] SL set: ${stop_loss:.4f}")
                return True
            except Exception as e:
                logging.error(f"  [ERROR] SL failed: {e}")
                return False
                
        except Exception as e:
            logging.error(f"Error setting protection for {symbol}: {e}")
            return False
    
    def check_and_protect(self):
        """Main protection loop - check all positions and protect them"""
        positions = self.get_all_positions()
        
        if not positions:
            logging.info("No open positions found")
            return
        
        logging.info(f"\n{'='*60}")
        logging.info(f"🔒 PROTECTION CHECK - {datetime.now().strftime('%H:%M:%S')}")
        logging.info(f"{'='*60}")
        logging.info(f"Found {len(positions)} position(s)")
        
        protected_count = 0
        needs_protection = 0
        
        for symbol, pos in positions.items():
            sl = pos['stop_loss']
            tp = pos['take_profit']
            side = pos['side']
            entry = pos['entry']
            pnl = pos['pnl']
            
            has_sl = sl is not None and float(sl) > 0
            has_tp = tp is not None and float(tp) > 0
            
            status_emoji = "🔒" if (has_sl and has_tp) else "⚠️"
            
            logging.info(f"\n{status_emoji} {symbol} | {side.upper()}")
            logging.info(f"   Entry: ${entry:.2f} | PnL: ${pnl:+.2f}")
            logging.info(f"   SL: {sl if has_sl else 'NOT SET'} | TP: {tp if has_tp else 'NOT SET'}")
            
            # Check if protection needed
            if not has_sl or not has_tp:
                needs_protection += 1
                logging.info(f"   🛡️  Setting protection...")
                if self.set_protection(symbol, pos):
                    protected_count += 1
                    self.protected_positions[symbol] = {
                        'time': datetime.now().isoformat(),
                        'entry': entry,
                        'side': side
                    }
            else:
                logging.info(f"   ✅ Already protected")
        
        logging.info(f"\n{'='*60}")
        logging.info(f"Protected: {protected_count}/{needs_protection} needed protection")
        logging.info(f"{'='*60}\n")
    
    def run(self):
        """Main loop - runs continuously"""
        logging.info("="*60)
        logging.info("BOSS33 AUTO PROTECTION SYSTEM - STARTED")
        logging.info("="*60)
        logging.info(f"Stop Loss: {PROTECTION['stop_loss_pct']}%")
        logging.info(f"Take Profit: {PROTECTION['take_profit_pct']}%")
        logging.info("="*60)
        
        try:
            while True:
                self.check_and_protect()
                time.sleep(20)  # Check every 20 seconds
        except KeyboardInterrupt:
            logging.info("\nProtection system stopped")

if __name__ == '__main__':
    manager = ProtectionManager()
    manager.run()
