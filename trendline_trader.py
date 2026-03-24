# Advanced Trendline Trading Bot for Bybit
# Strategy: Trendline bounce with RSI + Volume confirmation
# Risk: 1-2% per trade, Max 3 positions

import ccxt
import pandas as pd
import numpy as np
import talib
from scipy import stats
import time
from datetime import datetime, timedelta
import logging
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import trade notifier
try:
    from trade_notifier import notify_trade_opened, notify_trade_closed, notify_error
    NOTIFIER_AVAILABLE = True
except ImportError:
    NOTIFIER_AVAILABLE = False
    logging.warning("Trade notifier not available, Telegram notifications disabled")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trendline_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API Credentials
API_KEY = "bsK06QDhsagOWwFsXQ"
API_SECRET = "ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa"

class TrendlineTrader:
    def __init__(self):
        """Initialize trendline trader"""
        self.exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'},  # FUTURES trading
            # Try alternative API endpoint for geo-blocked regions
            'urls': {
                'api': {
                    'public': 'https://api.bytick.com',
                    'private': 'https://api.bytick.com',
                }
            }
        })
        self.exchange.load_markets()
        
        # Account settings - DYNAMIC (SMART) CONFIGURATION
        self.portfolio_value = 100.0  # $100 account
        self.risk_per_trade = 0.02  # 2% risk per trade (reduced from 3%)
        self.max_positions = 7
        self.rr_ratio = 1.5  # 1.5:1 for quick profits (was 2.5)
        
        # DYNAMIC TP/SL SETTINGS (Option 3: Smart)
        self.stop_loss_pct = 0.02  # Fixed 2% SL (was 4%)
        self.take_profit_pct = 0.03  # 3% initial TP
        self.partial_close_pct = 0.50  # Close 50% at 3% profit
        self.use_trailing_tp = True  # Trailing TP on remaining 50%
        self.trailing_tp_activation = 0.03  # Activate after 3% profit
        self.trailing_tp_distance = 0.01  # Trail 1% behind price
        
        logger.info("Trendline Trader initialized with DYNAMIC (SMART) settings")
        logger.info(f"SL: {self.stop_loss_pct*100}%, TP: {self.take_profit_pct*100}% (partial {self.partial_close_pct*100}%), Risk: {self.risk_per_trade*100}%")
    
    def fetch_data(self, symbol, timeframe='4h', limit=150):
        """Fetch OHLCV data"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return None
    
    def find_swing_points(self, df, window=5):
        """Find swing highs and lows"""
        highs = df['high'].values
        lows = df['low'].values
        
        swing_highs = []
        swing_lows = []
        
        for i in range(window, len(df) - window):
            # Swing high
            if all(highs[i] > highs[i-j] for j in range(1, window+1)) and \
               all(highs[i] > highs[i+j] for j in range(1, window+1)):
                swing_highs.append((i, highs[i], df['timestamp'].iloc[i]))
            
            # Swing low
            if all(lows[i] < lows[i-j] for j in range(1, window+1)) and \
               all(lows[i] < lows[i+j] for j in range(1, window+1)):
                swing_lows.append((i, lows[i], df['timestamp'].iloc[i]))
        
        return swing_highs, swing_lows
    
    def fit_trendline(self, points, tolerance=0.008):
        """Fit trendline through points with tolerance"""
        if len(points) < self.min_swings:
            return None
        
        x = np.array([p[0] for p in points])
        y = np.array([p[1] for p in points])
        
        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        # Check how many points touch the line within tolerance
        touches = 0
        for i, (idx, price, _) in enumerate(points):
            expected = slope * idx + intercept
            deviation = abs(price - expected) / expected
            if deviation <= tolerance:
                touches += 1
        
        if touches >= self.min_swings:
            return {
                'slope': slope,
                'intercept': intercept,
                'r_squared': r_value**2,
                'touches': touches,
                'points': points
            }
        
        return None
    
    def detect_trendlines(self, df):
        """Detect upward and downward trendlines"""
        swing_highs, swing_lows = self.find_swing_points(df)
        
        trendlines = {
            'support': [],  # Upward trendlines (connect swing lows)
            'resistance': []  # Downward trendlines (connect swing highs)
        }
        
        # Find support trendlines (connect swing lows)
        if len(swing_lows) >= self.min_swings:
            for i in range(len(swing_lows) - 2):
                for j in range(i + 2, len(swing_lows)):
                    points = swing_lows[i:j+1]
                    tl = self.fit_trendline(points, self.tolerance)
                    if tl and tl['slope'] > 0:  # Upward trend
                        trendlines['support'].append(tl)
        
        # Find resistance trendlines (connect swing highs)
        if len(swing_highs) >= self.min_swings:
            for i in range(len(swing_highs) - 2):
                for j in range(i + 2, len(swing_highs)):
                    points = swing_highs[i:j+1]
                    tl = self.fit_trendline(points, self.tolerance)
                    if tl and tl['slope'] < 0:  # Downward trend
                        trendlines['resistance'].append(tl)
        
        # Keep only strongest trendlines (highest R-squared)
        trendlines['support'].sort(key=lambda x: x['r_squared'], reverse=True)
        trendlines['resistance'].sort(key=lambda x: x['r_squared'], reverse=True)
        
        trendlines['support'] = trendlines['support'][:3]
        trendlines['resistance'] = trendlines['resistance'][:3]
        
        return trendlines
    
    def get_trendline_value(self, trendline, current_index):
        """Get trendline value at current index"""
        return trendline['slope'] * current_index + trendline['intercept']
    
    def check_trendline_touch(self, price, trendline_value, tolerance=0.008):
        """Check if price touched trendline within tolerance"""
        deviation = abs(price - trendline_value) / trendline_value
        return deviation <= tolerance
    
    def is_bullish_candle(self, open_price, close_price):
        """Check if candle is bullish"""
        return close_price > open_price
    
    def is_bearish_candle(self, open_price, close_price):
        """Check if candle is bearish"""
        return close_price < open_price
    
    def check_volume_confirmation(self, df, period=20):
        """Check if volume is above average"""
        current_volume = df['volume'].iloc[-1]
        avg_volume = df['volume'].rolling(window=period).mean().iloc[-1]
        return current_volume > (avg_volume * self.volume_mult)
    
    def check_entry_signal(self, df, trendlines):
        """Check for entry signals"""
        current_idx = len(df) - 1
        current_price = df['close'].iloc[-1]
        current_open = df['open'].iloc[-1]
        current_high = df['high'].iloc[-1]
        current_low = df['low'].iloc[-1]
        
        # Calculate RSI
        rsi = talib.RSI(df['close'].values, timeperiod=14)[-1]
        
        signals = []
        
        # LONG: Bounce off support trendline
        for tl in trendlines['support']:
            tl_value = self.get_trendline_value(tl, current_idx)
            
            # Price near trendline
            if current_low <= tl_value * 1.02:  # Within 2% below
                # RSI range for LONG
                if 25 <= rsi <= 55:
                    # SL: 2% below entry (fixed)
                    stop_loss = current_price * (1 - self.stop_loss_pct)
                    
                    # TP: 3% above entry (for partial close)
                    take_profit = current_price * (1 + self.take_profit_pct)
                    
                    risk = current_price - stop_loss
                    
                    # Ensure risk is reasonable
                    if risk <= 0 or risk > current_price * 0.05:  # Max 5% risk
                        continue
                    
                    signals.append({
                        'type': 'LONG',
                        'confidence': tl['r_squared'] * 100,
                        'entry': current_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'trendline_value': tl_value,
                        'rsi': rsi,
                        'reason': f"Support bounce, SL {self.stop_loss_pct*100}%, TP {self.take_profit_pct*100}%"
                    })
        
        # SHORT: Bounce off resistance trendline
        for tl in trendlines['resistance']:
            tl_value = self.get_trendline_value(tl, current_idx)
            
            # Price near trendline
            if current_high >= tl_value * 0.98:  # Within 2% above
                # RSI range for SHORT
                if 45 <= rsi <= 75:
                    # SL: 2% above entry (fixed)
                    stop_loss = current_price * (1 + self.stop_loss_pct)
                    
                    # TP: 3% below entry (for partial close)
                    take_profit = current_price * (1 - self.take_profit_pct)
                    
                    risk = stop_loss - current_price
                    
                    # Ensure risk is reasonable
                    if risk <= 0 or risk > current_price * 0.05:  # Max 5% risk
                        continue
                    
                    signals.append({
                        'type': 'SHORT',
                        'confidence': tl['r_squared'] * 100,
                        'entry': current_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'trendline_value': tl_value,
                        'rsi': rsi,
                        'reason': f"Resistance bounce, SL {self.stop_loss_pct*100}%, TP {self.take_profit_pct*100}%"
                    })
        
        return signals
    
    def calculate_position_size(self, entry, stop_loss, symbol):
        """Calculate position size based on risk, enforcing minimums"""
        risk_amount = self.portfolio_value * self.risk_per_trade
        price_risk = abs(entry - stop_loss)
        
        if price_risk == 0:
            return 0
        
        position_size = risk_amount / price_risk
        max_position = self.portfolio_value * 0.33 / entry  # Max 33% of portfolio
        
        # Get minimum for this symbol
        min_size = self.min_position_sizes.get(symbol, 0.01)
        
        # NEW: Ensure minimum $30 position value for high-priced coins
        min_position_value = 30.0
        min_by_value = min_position_value / entry
        
        # Use the larger of: calculated size, min size, or min by value
        final_size = max(position_size, min_size, min_by_value)
        final_size = min(final_size, max_position)
        
        # Round to appropriate precision for the symbol
        if symbol in ['BTCUSDT', 'ETHUSDT', 'LINKUSDT']:
            final_size = round(final_size, 3)
            # Ensure minimum after rounding
            if final_size < 0.015:
                final_size = 0.015
        elif symbol in ['SOLUSDT']:
            final_size = round(final_size, 1)
            if final_size < 1.0:
                final_size = 1.0
        else:
            final_size = round(final_size, 0)
        
        return final_size
    
    def execute_trade(self, signal):
        """Execute a trade on Bybit Futures with native TP/SL"""
        try:
            futures_symbol = signal['symbol']  # Already in futures format (BTCUSDT)
            
            # Check if position already exists for this symbol
            if futures_symbol in self.positions:
                logger.info(f"Skipping {futures_symbol}: Position already open (Entry: ${self.positions[futures_symbol]['entry']:.4f})")
                return
            
            side = 'Buy' if signal['type'] == 'LONG' else 'Sell'
            amount = self.calculate_position_size(signal['entry'], signal['stop_loss'], futures_symbol)
            
            # Check minimum position size
            min_size = self.min_position_sizes.get(futures_symbol, 0.01)
            if amount < min_size:
                logger.warning(f"Position size {amount} below minimum {min_size} for {futures_symbol}")
                return
            
            if amount <= 0:
                logger.warning(f"Invalid position size for {futures_symbol}")
                return
            
            logger.info(f"EXECUTING: {side} {amount} {futures_symbol} @ {signal['entry']}")
            
            # Create market order with TP/SL params
            order = self.exchange.create_order(
                futures_symbol,
                'market',
                side.lower(),
                amount,
                None,
                {
                    'stopLoss': str(signal['stop_loss']),
                    'takeProfit': str(signal['take_profit'])
                }
            )
            
            logger.info(f"ORDER EXECUTED: {order['id']}")
            logger.info(f"Entry: {order['average'] or order['price']}")
            logger.info(f"TP/SL SET: TP=${signal['take_profit']:.4f}, SL=${signal['stop_loss']:.4f}")
            
            # Store position
            entry_price = order['average'] or order['price'] or signal['entry']
            self.positions[futures_symbol] = {
                'side': signal['type'],
                'entry': entry_price,
                'amount': amount,
                'stop_loss': signal['stop_loss'],
                'take_profit': signal['take_profit'],
                'order_id': order['id'],
                'open_time': datetime.now()
            }
            
            # Send Telegram notification
            if NOTIFIER_AVAILABLE:
                try:
                    notify_trade_opened(
                        symbol=futures_symbol,
                        side=signal['type'],
                        amount=amount,
                        entry=entry_price,
                        stop_loss=signal['stop_loss'],
                        take_profit=signal['take_profit'],
                        bot_name="Trendline Bot"
                    )
                except Exception as e:
                    logger.error(f"Failed to send notification: {e}")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Trade execution failed: {error_msg}")
            # Don't send Telegram alert for balance errors (not actual errors)
            if NOTIFIER_AVAILABLE and "ab not enough" not in error_msg:
                try:
                    notify_error(error_msg, "Trendline Bot")
                except:
                    pass
    
    def run(self):
        """Main trading loop"""
        logger.info("="*70)
        logger.info("TRENDLINE TRADING BOT STARTED")
        logger.info("="*70)
        
        while True:
            try:
                # Scan ALL symbols - AGGRESSIVE
                for symbol in self.symbols:
                    df = self.fetch_data(symbol, '1h', 100)  # 1h timeframe instead of 4h
                    if df is None:
                        continue
                    
                    # Detect trendlines
                    trendlines = self.detect_trendlines(df)
                    
                    # Check for entry signals
                    signals = self.check_entry_signal(df, trendlines)
                    
                    if signals:
                        for signal in signals:
                            signal['symbol'] = symbol
                            readable = symbol.replace('USDT', '/USDT')
                            logger.info(f"SIGNAL: {readable} - {signal}")
                            # EXECUTE THE TRADE
                            self.execute_trade(signal)
                    else:
                        logger.info(f"{symbol}: No signals | Support: {len(trendlines['support'])}, Resistance: {len(trendlines['resistance'])}")
                
                # CHECK EXISTING POSITIONS FOR TP/SL
                self.check_positions()
                
                # Wait 5 minutes before next scan - AGGRESSIVE
                logger.info("Waiting 5 minutes for next scan...")
                time.sleep(300)
                
            except KeyboardInterrupt:
                logger.info("Trading stopped")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(30)

    def check_positions(self):
        """Check positions with trailing take profit"""
        for symbol in list(self.positions.keys()):
            try:
                position = self.positions[symbol]
                ticker = self.exchange.fetch_ticker(symbol)
                current_price = ticker['last']
                
                entry = position['entry']
                stop_loss = position['stop_loss']
                take_profit = position['take_profit']
                side = position['side']
                amount = position['amount']
                
                # Calculate current profit
                if side == 'LONG':
                    current_profit_pct = (current_price - entry) / entry
                    unrealized_pnl = (current_price - entry) * amount
                else:  # SHORT
                    current_profit_pct = (entry - current_price) / entry
                    unrealized_pnl = (entry - current_price) * amount
                
                logger.info(f"Checking {symbol}: Current=${current_price:.4f}, Entry=${entry:.4f}, "
                          f"TP=${take_profit:.4f}, SL=${stop_loss:.4f}, PnL=${unrealized_pnl:.2f} ({current_profit_pct*100:.2f}%)")
                
                # TRAILING TAKE PROFIT LOGIC
                if self.use_trailing_tp and current_profit_pct > self.trailing_tp_activation:
                    # Trailing activated - move take profit to lock in gains
                    
                    if side == 'LONG':
                        # For LONG: new TP = current_price * (1 - trailing_distance)
                        new_tp = current_price * (1 - self.trailing_tp_distance)
                        
                        # Only move TP up, never down
                        if new_tp > take_profit:
                            # Round to avoid micro-adjustments
                            new_tp = round(new_tp / self.trailing_tp_step) * self.trailing_tp_step
                            
                            if new_tp > take_profit:
                                position['take_profit'] = new_tp
                                logger.info(f"🎯 TRAILING TP UPDATED: {symbol} new TP=${new_tp:.4f} "
                                          f"(locked {current_profit_pct*100:.1f}% profit)")
                                
                                # Send notification when trailing TP activates
                                if NOTIFIER_AVAILABLE:
                                    try:
                                        notify_trade_opened(
                                            symbol=symbol,
                                            side=side,
                                            amount=amount,
                                            entry=entry,
                                            stop_loss=stop_loss,
                                            take_profit=new_tp,
                                            bot_name="🎯 Trendline Bot - Trailing TP"
                                        )
                                    except:
                                        pass
                    
                    else:  # SHORT
                        # For SHORT: new TP = current_price * (1 + trailing_distance)
                        new_tp = current_price * (1 + self.trailing_tp_distance)
                        
                        # Only move TP down, never up
                        if new_tp < take_profit:
                            # Round to avoid micro-adjustments
                            new_tp = round(new_tp / self.trailing_tp_step) * self.trailing_tp_step
                            
                            if new_tp < take_profit:
                                position['take_profit'] = new_tp
                                logger.info(f"🎯 TRAILING TP UPDATED: {symbol} new TP=${new_tp:.4f} "
                                          f"(locked {current_profit_pct*100:.1f}% profit)")
                                
                                # Send notification when trailing TP activates
                                if NOTIFIER_AVAILABLE:
                                    try:
                                        notify_trade_opened(
                                            symbol=symbol,
                                            side=side,
                                            amount=amount,
                                            entry=entry,
                                            stop_loss=stop_loss,
                                            take_profit=new_tp,
                                            bot_name="🎯 Trendline Bot - Trailing TP"
                                        )
                                    except:
                                        pass
                
                # Check if position hit stop loss or take profit
                # Minimum hold time: 5 minutes (prevent immediate closes)
                hold_time = (datetime.now() - position.get('open_time', datetime.now())).total_seconds()
                min_hold_time = 300  # 5 minutes
                
                if side == 'LONG':
                    if current_price <= stop_loss:
                        pnl = (current_price - entry) * amount
                        self.close_position(symbol, current_price, 'STOP LOSS', pnl, amount)
                    elif current_price >= take_profit and hold_time >= min_hold_time:
                        pnl = (current_price - entry) * amount
                        self.close_position(symbol, current_price, 'TAKE PROFIT', pnl, amount)
                    elif current_price >= take_profit and hold_time < min_hold_time:
                        logger.info(f"⏳ {symbol}: TP hit but holding for min time ({hold_time:.0f}s < {min_hold_time}s)")
                
                elif side == 'SHORT':
                    if current_price >= stop_loss:
                        pnl = (entry - current_price) * amount
                        self.close_position(symbol, current_price, 'STOP LOSS', pnl, amount)
                    elif current_price <= take_profit and hold_time >= min_hold_time:
                        pnl = (entry - current_price) * amount
                        self.close_position(symbol, current_price, 'TAKE PROFIT', pnl, amount)
                    elif current_price <= take_profit and hold_time < min_hold_time:
                        logger.info(f"⏳ {symbol}: TP hit but holding for min time ({hold_time:.0f}s < {min_hold_time}s)")
                
            except Exception as e:
                logger.error(f"Error checking position {symbol}: {e}")
    
    def close_position(self, symbol, exit_price, reason, pnl, amount):
        """Close position"""
        try:
            position = self.positions[symbol]
            side = 'sell' if position['side'] == 'LONG' else 'buy'
            
            # Track win/loss for win rate
            if not hasattr(self, 'total_trades'):
                self.total_trades = 0
                self.winning_trades = 0
            
            self.total_trades += 1
            if pnl > 0:
                self.winning_trades += 1
            
            win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
            
            # Close the position
            order = self.exchange.create_market_order(symbol, side, amount)
            
            msg = f"""
[POSITION CLOSED - {reason}]
Symbol: {symbol}
Side: {position['side']}
Entry: ${position['entry']:.4f}
Exit: ${exit_price:.4f}
PnL: ${pnl:.2f}
Win Rate: {win_rate:.1f}%
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            logger.info(msg)
            print(msg)
            
            # Send Telegram notification
            if NOTIFIER_AVAILABLE:
                try:
                    notify_trade_closed(
                        symbol=symbol,
                        side=position['side'],
                        entry=position['entry'],
                        exit_price=exit_price,
                        pnl=pnl,
                        reason=reason,
                        win_rate=win_rate,
                        bot_name="Trendline Bot"
                    )
                except Exception as e:
                    logger.error(f"Failed to send notification: {e}")
            
            del self.positions[symbol]
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")

if __name__ == "__main__":
    trader = TrendlineTrader()
    trader.run()
