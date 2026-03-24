# Trendline Trading Bot - FUTURES with 3x LEVERAGE
# Strategy: Trendline bounce with RSI + Volume confirmation
# Risk: 1-2% per trade on margin, Max 3 positions

import ccxt
import pandas as pd
import numpy as np
import talib
from scipy import stats
import time
from datetime import datetime, timedelta
import logging

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

class TrendlineFuturesTrader:
    def __init__(self):
        """Initialize trendline futures trader with 3x leverage"""
        self.exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',  # FUTURES trading
                'adjustForTimeDifference': True
            }
        })
        self.exchange.load_markets()
        
        # LEVERAGE SETTINGS
        self.leverage = 3  # 3x leverage
        
        # Account settings
        self.portfolio_value = 50.0  # $50 account
        self.risk_per_trade = 0.015  # 1.5% risk per trade ON MARGIN
        self.max_positions = 3
        self.rr_ratio = 2.0  # 2:1 risk-reward
        
        # Strategy parameters
        self.lookback = 100
        self.min_swings = 3
        self.tolerance = 0.008
        self.volume_mult = 1.5
        
        # Track state
        self.positions = {}
        self.trendlines = {}
        
        logger.info("Trendline Futures Trader initialized with 3x leverage")
    
    def set_leverage(self, symbol):
        """Set leverage for symbol"""
        try:
            self.exchange.set_leverage(self.leverage, symbol)
            logger.info(f"Leverage set to {self.leverage}x for {symbol}")
        except Exception as e:
            logger.info(f"Leverage already set or: {e}")
    
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
        """Fit trendline through points"""
        if len(points) < self.min_swings:
            return None
        
        x = np.array([p[0] for p in points])
        y = np.array([p[1] for p in points])
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
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
        """Detect trendlines"""
        swing_highs, swing_lows = self.find_swing_points(df)
        
        trendlines = {'support': [], 'resistance': []}
        
        if len(swing_lows) >= self.min_swings:
            for i in range(len(swing_lows) - 2):
                for j in range(i + 2, len(swing_lows)):
                    points = swing_lows[i:j+1]
                    tl = self.fit_trendline(points, self.tolerance)
                    if tl and tl['slope'] > 0:
                        trendlines['support'].append(tl)
        
        if len(swing_highs) >= self.min_swings:
            for i in range(len(swing_highs) - 2):
                for j in range(i + 2, len(swing_highs)):
                    points = swing_highs[i:j+1]
                    tl = self.fit_trendline(points, self.tolerance)
                    if tl and tl['slope'] < 0:
                        trendlines['resistance'].append(tl)
        
        trendlines['support'].sort(key=lambda x: x['r_squared'], reverse=True)
        trendlines['resistance'].sort(key=lambda x: x['r_squared'], reverse=True)
        
        trendlines['support'] = trendlines['support'][:3]
        trendlines['resistance'] = trendlines['resistance'][:3]
        
        return trendlines
    
    def get_trendline_value(self, trendline, current_index):
        """Get trendline value"""
        return trendline['slope'] * current_index + trendline['intercept']
    
    def check_volume_confirmation(self, df, period=20):
        """Check volume"""
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
        
        rsi = talib.RSI(df['close'].values, timeperiod=14)[-1]
        
        signals = []
        
        # LONG: Bounce off support
        for tl in trendlines['support']:
            tl_value = self.get_trendline_value(tl, current_idx)
            
            if current_low <= tl_value * 1.02:
                if current_price > current_open:  # Bullish
                    if 30 <= rsi <= 50:
                        if self.check_volume_confirmation(df):
                            stop_loss = tl_value * 0.97
                            risk = current_price - stop_loss
                            take_profit = current_price + (risk * self.rr_ratio)
                            
                            signals.append({
                                'type': 'LONG',
                                'confidence': tl['r_squared'] * 100,
                                'entry': current_price,
                                'stop_loss': stop_loss,
                                'take_profit': take_profit,
                                'trendline_value': tl_value,
                                'rsi': rsi,
                                'reason': f"Support trendline bounce, RSI {rsi:.1f}"
                            })
        
        # SHORT: Bounce off resistance
        for tl in trendlines['resistance']:
            tl_value = self.get_trendline_value(tl, current_idx)
            
            if current_high >= tl_value * 0.98:
                if current_price < current_open:  # Bearish
                    if 50 <= rsi <= 70:
                        if self.check_volume_confirmation(df):
                            stop_loss = tl_value * 1.03
                            risk = stop_loss - current_price
                            take_profit = current_price - (risk * self.rr_ratio)
                            
                            signals.append({
                                'type': 'SHORT',
                                'confidence': tl['r_squared'] * 100,
                                'entry': current_price,
                                'stop_loss': stop_loss,
                                'take_profit': take_profit,
                                'trendline_value': tl_value,
                                'rsi': rsi,
                                'reason': f"Resistance trendline bounce, RSI {rsi:.1f}"
                            })
        
        return signals
    
    def calculate_position_size(self, entry, stop_loss):
        """Calculate position size with LEVERAGE"""
        # Risk amount in USDT
        risk_amount = self.portfolio_value * self.risk_per_trade
        
        # Price risk (absolute)
        price_risk = abs(entry - stop_loss)
        
        if price_risk == 0:
            return 0
        
        # Position size WITHOUT leverage
        position_size_no_lev = risk_amount / price_risk
        
        # With leverage, we can control larger position with same margin
        # position_size = position_size_no_lev (this is the CONTRACT size)
        position_size = position_size_no_lev
        
        # Max position value (33% of portfolio * leverage)
        max_position_value = self.portfolio_value * 0.33 * self.leverage
        max_position_size = max_position_value / entry
        
        return min(position_size, max_position_size)
    
    def open_position(self, symbol, side, amount, stop_loss, take_profit):
        """Open futures position"""
        try:
            # Set leverage first
            self.set_leverage(symbol)
            
            # Create market order
            if side == 'LONG':
                order = self.exchange.create_market_buy_order(symbol, amount)
            else:
                order = self.exchange.create_market_sell_order(symbol, amount)
            
            entry_price = order['price'] if order['price'] else order['average']
            
            # Calculate margin used
            position_value = amount * entry_price
            margin_used = position_value / self.leverage
            
            self.positions[symbol] = {
                'side': side,
                'amount': amount,
                'entry': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'margin': margin_used,
                'time': datetime.now()
            }
            
            msg = f"""
[FUTURES POSITION OPENED - {self.leverage}x LEVERAGE]
Symbol: {symbol}
Side: {side}
Entry: ${entry_price:.4f}
Size: {amount:.4f} contracts
Margin: ${margin_used:.2f} USDT
Leverage: {self.leverage}x
Stop Loss: ${stop_loss:.4f}
Take Profit: ${take_profit:.4f}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            logger.info(msg)
            print(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Error opening position: {e}")
            return False
    
    def check_positions(self):
        """Check and close positions"""
        for symbol in list(self.positions.keys()):
            try:
                position = self.positions[symbol]
                ticker = self.exchange.fetch_ticker(symbol)
                current_price = ticker['last']
                
                # Check stop loss
                if position['side'] == 'LONG':
                    if current_price <= position['stop_loss']:
                        pnl = (current_price - position['entry']) * position['amount']
                        self.close_position(symbol, current_price, 'STOP LOSS', pnl)
                    elif current_price >= position['take_profit']:
                        pnl = (current_price - position['entry']) * position['amount']
                        self.close_position(symbol, current_price, 'TAKE PROFIT', pnl)
                else:  # SHORT
                    if current_price >= position['stop_loss']:
                        pnl = (position['entry'] - current_price) * position['amount']
                        self.close_position(symbol, current_price, 'STOP LOSS', pnl)
                    elif current_price <= position['take_profit']:
                        pnl = (position['entry'] - current_price) * position['amount']
                        self.close_position(symbol, current_price, 'TAKE PROFIT', pnl)
                        
            except Exception as e:
                logger.error(f"Error checking position {symbol}: {e}")
    
    def close_position(self, symbol, exit_price, reason, pnl):
        """Close futures position"""
        try:
            position = self.positions[symbol]
            
            if position['side'] == 'LONG':
                order = self.exchange.create_market_sell_order(symbol, position['amount'])
            else:
                order = self.exchange.create_market_buy_order(symbol, position['amount'])
            
            # Calculate PnL with leverage effect
            pnl_pct = (pnl / (position['entry'] * position['amount'])) * 100
            pnl_with_lev = pnl * self.leverage
            
            msg = f"""
[FUTURES POSITION CLOSED - {self.leverage}x LEVERAGE]
Symbol: {symbol}
Side: {position['side']}
Entry: ${position['entry']:.4f}
Exit: ${exit_price:.4f}
Gross PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)
With {self.leverage}x Lev: ${pnl_with_lev:.2f}
Reason: {reason}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            logger.info(msg)
            print(msg)
            
            del self.positions[symbol]
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
    
    def scan_and_trade(self):
        """Main scan loop"""
        logger.info("Scanning futures markets for opportunities...")
        
        # Check existing positions
        self.check_positions()
        
        if len(self.positions) >= self.max_positions:
            logger.info(f"Max positions reached ({self.max_positions})")
            return
        
        # Trading pairs - futures only ( majors only, TRIA/ZAMA don't have futures yet)
        pairs = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'XRP/USDT:USDT']
        
        for symbol in pairs:
            if symbol in self.positions:
                continue
                
            df = self.fetch_data(symbol, '4h', 150)
            if df is None:
                continue
        
        # Detect trendlines
        trendlines = self.detect_trendlines(df)
        logger.info(f"Detected {len(trendlines['support'])} support, {len(trendlines['resistance'])} resistance trendlines")
        
        # Check signals
        signals = self.check_entry_signal(df, trendlines)
        
        if signals:
            for signal in signals:
                logger.info(f"SIGNAL: {signal}")
                
                if symbol in self.positions:
                    logger.info(f"Already in position for {symbol}")
                    continue
                
                amount = self.calculate_position_size(signal['entry'], signal['stop_loss'])
                
                if amount > 0:
                    self.open_position(
                        symbol,
                        signal['type'],
                        amount,
                        signal['stop_loss'],
                        signal['take_profit']
                    )
        else:
            logger.info("No entry signals found")
    
    def run(self):
        """Main loop"""
        logger.info("="*70)
        logger.info(f"TRENDLINE FUTURES TRADER STARTED - {self.leverage}x LEVERAGE")
        logger.info("="*70)
        
        while True:
            try:
                self.scan_and_trade()
                logger.info("Waiting for next 4h candle...")
                time.sleep(900)  # 15 minutes
                
            except KeyboardInterrupt:
                logger.info("Trading stopped")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(60)

if __name__ == "__main__":
    trader = TrendlineFuturesTrader()
    trader.run()
