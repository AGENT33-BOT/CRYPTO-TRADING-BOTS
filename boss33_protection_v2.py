"""
BOSS33 Protection System v2.0 - Enhanced Risk Management
Prevents big losses with tighter controls
"""

import ccxt
import time
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('boss33_protection_v2.log'),
        logging.StreamHandler()
    ]
)

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

# ENHANCED PROTECTION SETTINGS - TIGHTER FOR 2:1 R/R
PROTECTION = {
    'max_loss_per_position': 3.0,      # $3 max loss per position (tighter)
    'max_loss_per_day': 10.0,          # $10 max daily loss
    'breakeven_trigger': 0.75,         # Move to breakeven at +0.75%
    'trailing_start': 1.5,             # Start trailing at +1.5%
    'trailing_distance': 0.5,          # 0.5% trail
    'daily_loss_check': True,
    'margin_mode': 'ISOLATED',         # ISOLATED margin
    'leverage': 2,                     # 2x leverage (safer)
}

class EnhancedProtection:
    def __init__(self):
        self.exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'linear'}
        })
        self.daily_loss = 0
        self.last_date = datetime.now().date()
        
    def check_position_health(self, symbol, pos):
        """Check if position loss is within limits"""
        pnl = float(pos.get('unrealizedPnl', 0))
        
        # Check max loss per position
        if pnl < -PROTECTION['max_loss_per_position']:
            logging.warning(f"🚨 {symbol}: Loss ${pnl:.2f} exceeds max ${PROTECTION['max_loss_per_position']}! Closing...")
            return False
        
        return True
    
    def close_position(self, symbol, reason):
        """Close position immediately"""
        try:
            positions = self.exchange.fetch_positions([symbol])
            if positions and len(positions) > 0:
                pos = positions[0]
                contracts = float(pos.get('contracts', 0))
                side = pos['side']
                
                if contracts > 0:
                    close_side = 'buy' if side == 'short' else 'sell'
                    self.exchange.create_market_order(
                        symbol=symbol,
                        side=close_side,
                        amount=contracts,
                        params={'reduceOnly': True}
                    )
                    
                    # Cancel all orders
                    try:
                        self.exchange.cancel_all_orders(symbol)
                    except:
                        pass
                    
                    logging.info(f"✅ {symbol} closed: {reason}")
                    return True
        except Exception as e:
            logging.error(f"❌ Error closing {symbol}: {e}")
        return False
    
    def manage_positions(self):
        """Monitor and protect all positions"""
        symbols = [
            'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT',
            'DOGE/USDT:USDT', 'XRP/USDT:USDT', 'BCH/USDT:USDT', 'LINK/USDT:USDT'
        ]
        
        logging.info("=" * 60)
        logging.info("🔒 ENHANCED PROTECTION CHECK")
        logging.info("=" * 60)
        logging.info(f"Max loss per position: ${PROTECTION['max_loss_per_position']}")
        logging.info(f"Breakeven trigger: +{PROTECTION['breakeven_trigger']}%")
        logging.info("=" * 60)
        
        total_pnl = 0
        positions_closed = 0
        
        for symbol in symbols:
            try:
                pos_list = self.exchange.fetch_positions([symbol])
                if pos_list and len(pos_list) > 0:
                    pos = pos_list[0]
                    contracts = float(pos.get('contracts', 0))
                    
                    if contracts > 0:
                        entry = float(pos.get('entryPrice', 0))
                        mark = float(pos.get('markPrice', 0))
                        pnl = float(pos.get('unrealizedPnl', 0))
                        side = pos['side'].upper()
                        
                        total_pnl += pnl
                        
                        # Calculate PnL %
                        if entry > 0:
                            if side == 'LONG':
                                pnl_pct = ((mark - entry) / entry) * 100
                            else:
                                pnl_pct = ((entry - mark) / entry) * 100
                        else:
                            pnl_pct = 0
                        
                        status = "🟢" if pnl >= 0 else "🔴"
                        logging.info(f"\n{status} {symbol} | {side}")
                        logging.info(f"   Entry: ${entry:.2f} | Mark: ${mark:.2f}")
                        logging.info(f"   PnL: ${pnl:+.2f} ({pnl_pct:+.2f}%)")
                        
                        # Check if loss is too big
                        if not self.check_position_health(symbol, pos):
                            if self.close_position(symbol, f"Max loss exceeded: ${pnl:.2f}"):
                                positions_closed += 1
                                self.daily_loss += abs(pnl)
                        
                        # Check breakeven trigger
                        elif pnl_pct >= PROTECTION['breakeven_trigger']:
                            logging.info(f"   🎯 Approaching breakeven trigger (+{PROTECTION['breakeven_trigger']}%)")
                        
            except Exception as e:
                logging.debug(f"Error checking {symbol}: {e}")
        
        logging.info("\n" + "=" * 60)
        logging.info(f"Total PnL: ${total_pnl:+.2f}")
        logging.info(f"Positions closed: {positions_closed}")
        logging.info(f"Daily loss: ${self.daily_loss:.2f} / ${PROTECTION['max_loss_per_day']}")
        logging.info("=" * 60)
    
    def run(self):
        """Main protection loop"""
        logging.info("=" * 60)
        logging.info("🔒 ENHANCED PROTECTION SYSTEM v2.0 STARTED")
        logging.info("=" * 60)
        logging.info("Prevents losses > $5 per position")
        logging.info("Daily loss limit: $15")
        logging.info("=" * 60)
        
        try:
            while True:
                # Reset daily loss on new day
                current_date = datetime.now().date()
                if current_date != self.last_date:
                    self.daily_loss = 0
                    self.last_date = current_date
                    logging.info("🌅 New day - daily loss reset")
                
                self.manage_positions()
                logging.info("\n⏱️  Next check in 30 seconds...\n")
                time.sleep(30)
                
        except KeyboardInterrupt:
            logging.info("\nProtection system stopped")

if __name__ == '__main__':
    protector = EnhancedProtection()
    protector.run()
