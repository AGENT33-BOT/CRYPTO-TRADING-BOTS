"""
SIMPLE BREAKOUT STRATEGY v3.0
Only trade 4H breakouts with clear support/resistance
"""

import ccxt
import time
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('breakout_trader.log'),
        logging.StreamHandler()
    ]
)

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

# ULTRA SIMPLE CONFIG
CONFIG = {
    'max_positions': 1,         # ONLY 1 position at a time
    'risk_per_trade': 1.0,      # Risk 1% max
    'leverage': 1,              # NO LEVERAGE (safest)
    'check_interval': 300,      # Check every 5 minutes (not every 30s!)
    
    # TP/SL - Keep it simple
    'take_profit_pct': 0.05,    # 5% TP (let winners run)
    'stop_loss_pct': 0.025,     # 2.5% SL (cut losses fast)
    
    # Minimum setup quality
    'min_consolidation_hours': 12,  # Price must be flat for 12+ hours
    'breakout_volume_mult': 1.5,    # Volume must be 1.5x average
}

# ONLY 3 BEST PAIRS
PAIRS = [
    'BTC/USDT:USDT',   # Most reliable
    'ETH/USDT:USDT',   # Second best
    'SOL/USDT:USDT',   # Third option
]

class BreakoutTrader:
    def __init__(self):
        self.exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'linear'}
        })
        self.in_position = False
        
        logging.info("="*70)
        logging.info("BREAKOUT TRADER v3.0 - SIMPLIFIED")
        logging.info("Only 1 position, no leverage, 5% TP / 2.5% SL")
        logging.info("="*70)
    
    def get_balance(self):
        try:
            balance = self.exchange.fetch_balance()
            return float(balance['USDT']['free'])
        except:
            return 0
    
    def has_position(self):
        """Check if we have any position open"""
        for symbol in PAIRS:
            try:
                pos = self.exchange.fetch_positions([symbol])
                if pos and len(pos) > 0:
                    if float(pos[0].get('contracts', 0)) > 0:
                        return True, symbol
            except:
                pass
        return False, None
    
    def find_breakout_setup(self, symbol):
        """Look for consolidation + breakout pattern"""
        try:
            # Get 4H data (higher timeframe = better setups)
            ohlcv = self.exchange.fetch_ohlcv(symbol, '4h', limit=50)
            if len(ohlcv) < 30:
                return None
            
            highs = [c[2] for c in ohlcv]
            lows = [c[3] for c in ohlcv]
            closes = [c[4] for c in ohlcv]
            volumes = [c[5] for c in ohlcv]
            
            current_price = closes[-1]
            current_volume = volumes[-1]
            
            # Find consolidation range (last 12 candles = 48 hours)
            recent_highs = highs[-12:]
            recent_lows = lows[-12:]
            
            range_high = max(recent_highs[:-1])  # Exclude current candle
            range_low = min(recent_lows[:-1])
            range_size = (range_high - range_low) / range_low
            
            # Check if consolidating (range not too big)
            if range_size > 0.08:  # More than 8% range = not consolidated
                return None
            
            # Check volume
            avg_volume = sum(volumes[-12:-1]) / 11
            if current_volume < avg_volume * CONFIG['breakout_volume_mult']:
                return None
            
            # Check for breakout
            breakout_up = current_price > range_high and closes[-2] <= range_high
            breakout_down = current_price < range_low and closes[-2] >= range_low
            
            if breakout_up:
                return {
                    'symbol': symbol,
                    'direction': 'LONG',
                    'entry': current_price,
                    'stop': range_low,  # Stop below consolidation
                    'target': current_price + (current_price - range_low) * 2,  # 2:1 reward
                    'range_high': range_high,
                    'range_low': range_low
                }
            
            if breakout_down:
                return {
                    'symbol': symbol,
                    'direction': 'SHORT',
                    'entry': current_price,
                    'stop': range_high,  # Stop above consolidation
                    'target': current_price - (range_high - current_price) * 2,  # 2:1 reward
                    'range_high': range_high,
                    'range_low': range_low
                }
            
            return None
            
        except Exception as e:
            return None
    
    def open_position(self, setup):
        """Open breakout position"""
        try:
            symbol = setup['symbol']
            direction = setup['direction']
            entry = setup['entry']
            stop = setup['stop']
            target = setup['target']
            
            # Calculate position size based on risk
            balance = self.get_balance()
            risk_amount = balance * (CONFIG['risk_per_trade'] / 100)
            
            stop_distance = abs(entry - stop)
            if stop_distance == 0:
                return False
            
            position_size = risk_amount / stop_distance
            
            # Get market precision
            market = self.exchange.market(symbol)
            amount_precision = market['precision']['amount']
            position_size = round(position_size, int(-amount_precision) if amount_precision < 1 else 0)
            
            if position_size < market['limits']['amount']['min']:
                logging.warning(f"Position size too small")
                return False
            
            # Calculate SL % from entry
            sl_pct = abs(entry - stop) / entry
            tp_pct = abs(target - entry) / entry
            
            logging.info("="*70)
            logging.info(f"🚀 BREAKOUT {direction} - {symbol}")
            logging.info(f"Entry: ${entry:.2f}")
            logging.info(f"Stop: ${stop:.2f} ({sl_pct*100:.1f}%)")
            logging.info(f"Target: ${target:.2f} ({tp_pct*100:.1f}%)")
            logging.info(f"Size: {position_size}")
            logging.info(f"Leverage: {CONFIG['leverage']}x (NO LEVERAGE)")
            logging.info("="*70)
            
            # Set no leverage
            try:
                self.exchange.set_leverage(1, symbol)
            except:
                pass
            
            # Open position
            order = self.exchange.create_market_order(
                symbol=symbol,
                side='buy' if direction == 'LONG' else 'sell',
                amount=position_size
            )
            
            # Set SL
            tp_sl_side = 'sell' if direction == 'LONG' else 'buy'
            self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=tp_sl_side,
                amount=position_size,
                params={
                    'triggerPrice': round(stop, 4),
                    'reduceOnly': True
                }
            )
            
            # Set TP
            self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=tp_sl_side,
                amount=position_size,
                params={
                    'triggerPrice': round(target, 4),
                    'reduceOnly': True
                }
            )
            
            logging.info(f"✅ Position opened! Waiting for 5% profit or 2.5% loss...")
            self.in_position = True
            return True
            
        except Exception as e:
            logging.error(f"❌ Error: {e}")
            return False
    
    def run(self):
        """Main loop"""
        logging.info("Breakout trader running...")
        logging.info("Waiting for clean consolidation + breakout setups...")
        
        while True:
            try:
                # Check if we have position
                has_pos, current_symbol = self.has_position()
                
                if has_pos:
                    logging.info(f"In position: {current_symbol}. Monitoring...")
                    self.in_position = True
                else:
                    self.in_position = False
                    logging.info("No position. Looking for breakout setup...")
                    
                    # Look for setups on each pair
                    for symbol in PAIRS:
                        setup = self.find_breakout_setup(symbol)
                        if setup:
                            logging.info(f"Found breakout setup on {symbol}!")
                            self.open_position(setup)
                            break  # Only take 1 setup
                
                logging.info(f"\nNext check in {CONFIG['check_interval']}s...\n")
                time.sleep(CONFIG['check_interval'])
                
            except KeyboardInterrupt:
                logging.info("Stopped")
                break
            except Exception as e:
                logging.error(f"Error: {e}")
                time.sleep(CONFIG['check_interval'])

if __name__ == '__main__':
    trader = BreakoutTrader()
    trader.run()
