"""
TREND FOLLOWING AUTO TRADER v2.0
New strategy: Trade WITH the trend, not against it
"""

import ccxt
import time
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('trend_trader_v2.log'),
        logging.StreamHandler()
    ]
)

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

# NEW CONFIGURATION - TREND FOLLOWING WITH DOLLAR TP/SL
CONFIG = {
    'min_confidence': 80,       # Higher threshold
    
    # DOLLAR-BASED TP/SL (More reliable than percentages)
    'use_dollar_tp_sl': True,   # Use dollar targets instead of %
    'take_profit_usd': 2.00,    # Close at $2 profit
    'stop_loss_usd': 1.50,      # Close at $1.50 loss
    
    # Percentage-based fallback (if dollar targets not hit)
    'take_profit_pct': 0.03,    # 3% TP (fallback)
    'stop_loss_pct': 0.015,     # 1.5% SL (fallback)
    
    # Trailing stop
    'trailing_start_usd': 1.50, # Start trailing at $1.50 profit
    'trailing_distance_usd': 0.50,  # Trail $0.50 behind peak
    
    'risk_per_trade': 1.5,      # 1.5% of balance
    'max_positions': 3,         # MAX 3 positions
    'check_interval': 30,       # Check every 30 seconds (faster monitoring)
    'margin_mode': 'ISOLATED',
    'leverage': 2,              # 2x leverage
    'cooldown_minutes': 60,     # 1 hour cooldown
}

# FOCUS ON BEST PAIRS ONLY (not 90+)
PAIRS = [
    'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT',
    'AVAX/USDT:USDT', 'LINK/USDT:USDT', 'MATIC/USDT:USDT',
    'DOT/USDT:USDT', 'ATOM/USDT:USDT', 'NEAR/USDT:USDT',
    'XRP/USDT:USDT', 'DOGE/USDT:USDT', 'ADA/USDT:USDT'
]

class TrendFollowingTrader:
    def __init__(self):
        self.exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'linear'}
        })
        self.last_close_time = {}
        self.btc_trend = None
        
        logging.info("="*70)
        logging.info("TREND FOLLOWING TRADER v2.0 STARTED")
        logging.info("Strategy: Trade WITH the trend, not against it")
        logging.info("="*70)
    
    def get_btc_trend(self):
        """Check BTC trend on 1H timeframe - only trade alts in same direction"""
        try:
            ohlcv = self.exchange.fetch_ohlcv('BTC/USDT:USDT', '1h', limit=50)
            if len(ohlcv) < 50:
                return None
            
            closes = [c[4] for c in ohlcv]
            
            # EMA 20 and 50
            ema20 = sum(closes[-20:]) / 20
            ema50 = sum(closes[-50:]) / 50
            
            # Determine trend
            if ema20 > ema50 * 1.01:  # EMA20 above EMA50 by 1%
                return 'BULLISH'
            elif ema20 < ema50 * 0.99:  # EMA20 below EMA50 by 1%
                return 'BEARISH'
            else:
                return 'NEUTRAL'
                
        except Exception as e:
            logging.error(f"Error checking BTC trend: {e}")
            return None
    
    def analyze_pair(self, symbol):
        """Analyze pair for trend-following entry"""
        try:
            # Only trade in direction of BTC trend
            if self.btc_trend == 'NEUTRAL':
                return None
            
            # Fetch 1H data (higher timeframe = better signals)
            ohlcv = self.exchange.fetch_ohlcv(symbol, '1h', limit=50)
            if len(ohlcv) < 50:
                return None
            
            closes = [c[4] for c in ohlcv]
            highs = [c[2] for c in ohlcv]
            lows = [c[3] for c in ohlcv]
            volumes = [c[5] for c in ohlcv]
            
            current_price = closes[-1]
            
            # Calculate EMAs
            ema9 = sum(closes[-9:]) / 9
            ema21 = sum(closes[-21:]) / 21
            
            # RSI
            rsi = self.calculate_rsi(closes)
            
            # Volume check (need volume to confirm trend)
            avg_volume = sum(volumes[-10:]) / 10
            current_volume = volumes[-1]
            volume_ok = current_volume > avg_volume * 0.8
            
            signal = None
            confidence = 0
            
            # LONG Signal (Only if BTC is bullish)
            if self.btc_trend == 'BULLISH':
                # EMA9 crosses above EMA21 (bullish crossover)
                prev_ema9 = sum(closes[-10:-1]) / 9
                prev_ema21 = sum(closes[-22:-1]) / 21
                
                if ema9 > ema21 and prev_ema9 <= prev_ema21:
                    if rsi > 50 and rsi < 75 and volume_ok:
                        signal = 'LONG'
                        confidence = 80 + (rsi - 50) * 0.5
                        logging.info(f"{symbol}: EMA CROSSOVER LONG signal")
            
            # SHORT Signal (Only if BTC is bearish)
            elif self.btc_trend == 'BEARISH':
                # EMA9 crosses below EMA21 (bearish crossover)
                prev_ema9 = sum(closes[-10:-1]) / 9
                prev_ema21 = sum(closes[-22:-1]) / 21
                
                if ema9 < ema21 and prev_ema9 >= prev_ema21:
                    if rsi < 50 and rsi > 25 and volume_ok:
                        signal = 'SHORT'
                        confidence = 80 + (50 - rsi) * 0.5
                        logging.info(f"{symbol}: EMA CROSSOVER SHORT signal")
            
            if signal and confidence >= CONFIG['min_confidence']:
                return {
                    'symbol': symbol,
                    'signal': signal,
                    'confidence': min(confidence, 95),
                    'price': current_price,
                    'rsi': rsi,
                    'btc_trend': self.btc_trend
                }
            
            return None
            
        except Exception as e:
            return None
    
    def calculate_rsi(self, closes, period=14):
        """Calculate RSI"""
        if len(closes) < period + 1:
            return 50
        
        gains = []
        losses = []
        
        for i in range(1, period + 1):
            change = closes[-i] - closes[-(i+1)]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def get_balance(self):
        """Get account balance"""
        try:
            balance = self.exchange.fetch_balance()
            return float(balance['USDT']['free'])
        except:
            return 0
    
    def get_positions_count(self):
        """Count active positions"""
        count = 0
        for symbol in PAIRS:
            try:
                positions = self.exchange.fetch_positions([symbol])
                if positions and len(positions) > 0:
                    if float(positions[0].get('contracts', 0)) > 0:
                        count += 1
            except:
                pass
        return count
    
    def check_cooldown(self, symbol):
        """Check if symbol is in cooldown"""
        if symbol not in self.last_close_time:
            return True, 0
        
        elapsed = time.time() - self.last_close_time[symbol]
        cooldown_seconds = CONFIG['cooldown_minutes'] * 60
        
        if elapsed >= cooldown_seconds:
            return True, 0
        
        remaining = cooldown_seconds - elapsed
        return False, remaining
    
    def open_position(self, symbol, side, entry_price, confidence):
        """Open position with protection"""
        try:
            # Check cooldown
            can_trade, remaining = self.check_cooldown(symbol)
            if not can_trade:
                minutes_left = remaining / 60
                logging.info(f"{symbol}: In cooldown ({minutes_left:.0f}min remaining)")
                return False
            
            balance = self.get_balance()
            if balance < 20:
                logging.warning(f"Insufficient balance: ${balance:.2f}")
                return False
            
            # Calculate position size
            risk_amount = balance * (CONFIG['risk_per_trade'] / 100)
            stop_distance = entry_price * CONFIG['stop_loss_pct']
            position_size = risk_amount / stop_distance
            
            # Get market info
            market = self.exchange.market(symbol)
            amount_precision = market['precision']['amount']
            position_size = round(position_size, int(-amount_precision) if amount_precision < 1 else 0)
            
            if position_size < market['limits']['amount']['min']:
                logging.warning(f"Position size too small")
                return False
            
            # Calculate TP/SL
            if side == 'LONG':
                stop_loss = entry_price * (1 - CONFIG['stop_loss_pct'])
                take_profit = entry_price * (1 + CONFIG['take_profit_pct'])
            else:
                stop_loss = entry_price * (1 + CONFIG['stop_loss_pct'])
                take_profit = entry_price * (1 - CONFIG['take_profit_pct'])
            
            logging.info("="*70)
            logging.info(f"OPENING {side} POSITION - {symbol}")
            logging.info(f"BTC Trend: {self.btc_trend}")
            logging.info(f"Confidence: {confidence:.1f}%")
            logging.info(f"Entry: ${entry_price:.4f}")
            logging.info(f"Size: {position_size}")
            logging.info(f"Leverage: {CONFIG['leverage']}x")
            logging.info(f"SL: ${stop_loss:.4f} ({CONFIG['stop_loss_pct']*100:.1f}%)")
            logging.info(f"TP: ${take_profit:.4f} ({CONFIG['take_profit_pct']*100:.1f}%)")
            logging.info("="*70)
            
            # Set leverage and margin
            try:
                self.exchange.set_leverage(CONFIG['leverage'], symbol)
            except:
                pass
            
            try:
                self.exchange.set_margin_mode(CONFIG['margin_mode'], symbol)
            except:
                pass
            
            # Open position
            order = self.exchange.create_market_order(
                symbol=symbol,
                side='buy' if side == 'LONG' else 'sell',
                amount=position_size
            )
            
            # Set TP/SL
            tp_sl_side = 'sell' if side == 'LONG' else 'buy'
            
            # Stop Loss
            self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=tp_sl_side,
                amount=position_size,
                params={
                    'triggerPrice': round(stop_loss, 4),
                    'triggerDirection': 'descending' if side == 'LONG' else 'ascending',
                    'reduceOnly': True
                }
            )
            
            # Take Profit
            self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=tp_sl_side,
                amount=position_size,
                params={
                    'triggerPrice': round(take_profit, 4),
                    'triggerDirection': 'ascending' if side == 'LONG' else 'descending',
                    'reduceOnly': True
                }
            )
            
            logging.info(f"✅ {symbol} {side} position opened successfully!")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error opening position: {e}")
            return False
    
    def close_position(self, symbol, reason):
        """Close position immediately"""
        try:
            pos = self.exchange.fetch_positions([symbol])
            if pos and len(pos) > 0:
                contracts = float(pos[0].get('contracts', 0))
                side = pos[0]['side']
                if contracts > 0:
                    close_side = 'buy' if side == 'short' else 'sell'
                    self.exchange.create_market_order(
                        symbol=symbol,
                        side=close_side,
                        amount=contracts,
                        params={'reduceOnly': True}
                    )
                    self.exchange.cancel_all_orders(symbol)
                    self.last_close_time[symbol] = time.time()
                    logging.info(f"✅ CLOSED: {symbol} | Reason: {reason}")
                    return True
        except Exception as e:
            logging.error(f"❌ Error closing {symbol}: {e}")
        return False
    
    def monitor_positions(self):
        """Monitor positions for dollar TP/SL"""
        try:
            for symbol in PAIRS:
                try:
                    pos = self.exchange.fetch_positions([symbol])
                    if not pos or len(pos) == 0:
                        continue
                    
                    contracts = float(pos[0].get('contracts', 0))
                    if contracts <= 0:
                        continue
                    
                    pnl = float(pos[0].get('unrealizedPnl', 0))
                    side = pos[0]['side'].upper()
                    entry = float(pos[0].get('entryPrice', 0))
                    mark = float(pos[0].get('markPrice', 0))
                    
                    # DOLLAR TP/SL CHECK
                    if CONFIG['use_dollar_tp_sl']:
                        # Take Profit at $2
                        if pnl >= CONFIG['take_profit_usd']:
                            logging.info(f"💰 {symbol}: Profit ${pnl:.2f} reached! Taking profit...")
                            self.close_position(symbol, f"TP hit: ${pnl:.2f}")
                            continue
                        
                        # Stop Loss at -$1.50
                        if pnl <= -CONFIG['stop_loss_usd']:
                            logging.info(f"🛑 {symbol}: Loss ${abs(pnl):.2f} reached! Stopping out...")
                            self.close_position(symbol, f"SL hit: ${pnl:.2f}")
                            continue
                        
                        # Show progress
                        if pnl > 1.0:
                            logging.info(f"📈 {symbol}: Profit ${pnl:.2f} (need ${CONFIG['take_profit_usd']-pnl:.2f} more)")
                        elif pnl < -0.5:
                            logging.info(f"📉 {symbol}: Loss ${pnl:.2f} (limit -${CONFIG['stop_loss_usd']:.2f})")
                        
                except:
                    pass
                    
        except Exception as e:
            logging.error(f"Error monitoring positions: {e}")
    
    def scan_and_trade(self):
        """Main scanning loop"""
        # Update BTC trend first
        self.btc_trend = self.get_btc_trend()
        
        if not self.btc_trend or self.btc_trend == 'NEUTRAL':
            logging.info(f"BTC trend: {self.btc_trend} - No trading")
            return
        
        logging.info("="*70)
        logging.info(f"BTC TREND: {self.btc_trend} - Scanning for {self.btc_trend} setups")
        logging.info("="*70)
        
        # Check position count
        pos_count = self.get_positions_count()
        logging.info(f"Active positions: {pos_count}/{CONFIG['max_positions']}")
        
        if pos_count >= CONFIG['max_positions']:
            logging.info("Max positions reached. Skipping scan.")
            return
        
        # Scan each pair
        signals_found = []
        for symbol in PAIRS:
            result = self.analyze_pair(symbol)
            if result:
                signals_found.append(result)
        
        # Sort by confidence
        signals_found.sort(key=lambda x: x['confidence'], reverse=True)
        
        if signals_found:
            logging.info(f"Found {len(signals_found)} signals:")
            for sig in signals_found:
                logging.info(f"  {sig['symbol']}: {sig['signal']} ({sig['confidence']:.1f}%) | RSI: {sig['rsi']:.1f}")
            
            # Execute best signal
            best = signals_found[0]
            if best['confidence'] >= CONFIG['min_confidence']:
                logging.info(f"\n🚀 EXECUTING: {best['symbol']} {best['signal']} at {best['confidence']:.1f}%")
                self.open_position(best['symbol'], best['signal'], best['price'], best['confidence'])
        else:
            logging.info("No high-confidence trend signals found.")
    
    def run(self):
        """Main loop"""
        logging.info("Trend Following Trader running with Dollar TP/SL...")
        logging.info(f"TP: ${CONFIG['take_profit_usd']:.2f} | SL: ${CONFIG['stop_loss_usd']:.2f}")
        
        while True:
            try:
                # Monitor existing positions (dollar TP/SL)
                self.monitor_positions()
                
                # Scan for new opportunities
                self.scan_and_trade()
                
                logging.info(f"\nNext check in {CONFIG['check_interval']}s...\n")
                time.sleep(CONFIG['check_interval'])
            except KeyboardInterrupt:
                logging.info("\nTrader stopped")
                break
            except Exception as e:
                logging.error(f"Error: {e}")
                time.sleep(CONFIG['check_interval'])

if __name__ == '__main__':
    trader = TrendFollowingTrader()
    trader.run()
