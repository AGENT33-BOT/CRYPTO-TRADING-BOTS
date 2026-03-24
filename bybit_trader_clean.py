# Bybit Professional Trader - NO UNICODE VERSION
import ccxt
import pandas as pd
import numpy as np
import talib
import time
from datetime import datetime
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

# Setup logging - NO UNICODE
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bybit_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API Credentials
API_KEY = "bsK06QDhsagOWwFsXQ"
API_SECRET = "ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa"

class BybitTrader:
    def __init__(self):
        """Initialize Bybit connection"""
        try:
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
            logger.info("Connected to Bybit successfully")
            
            # Trading Parameters - AGGRESSIVE SETTINGS
            self.initial_balance = 49.95
            self.max_position_size = 20.0  # Increased from 12
            self.max_open_positions = 4  # Increased from 2
            self.stop_loss_pct = 0.025  # Tighter stop (was 0.04)
            self.take_profit_pct = 0.05  # Faster profits (was 0.08)
            
            # TRAILING TAKE PROFIT SETTINGS
            self.use_trailing_tp = True  # Enable trailing take profit
            self.trailing_tp_activation = 0.015  # Activate after 1.5% profit
            self.trailing_tp_distance = 0.01  # Trail 1% behind price
            
            # Trading pairs - FUTURES symbols (BTCUSDT format)
            self.pairs = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT', 'DOGEUSDT', 'LINKUSDT', 'NEARUSDT']
            
            # LEVERAGE for futures
            self.leverage = 3  # 3x leverage
            
            # Set leverage for each pair
            for pair in self.pairs:
                try:
                    self.exchange.set_leverage(self.leverage, pair)
                    logger.info(f"Leverage set to {self.leverage}x for {pair}")
                except Exception as e:
                    logger.warning(f"Could not set leverage for {pair}: {e}")
            
            # Track state
            self.positions = {}
            self.daily_pnl = 0.0
            self.total_trades = 0
            self.winning_trades = 0
            
            logger.info("Bybit Trader initialized")
            logger.info(f"Trailing TP enabled: {self.use_trailing_tp} (activation at {self.trailing_tp_activation*100}%, trail distance {self.trailing_tp_distance*100}%)")
            
        except Exception as e:
            logger.error(f"Failed to connect: {str(e)}")
            raise
    
    def get_balance(self):
        """Get USDT balance"""
        try:
            balance = self.exchange.fetch_balance()
            usdt = balance.get('USDT', {})
            free = usdt.get('free', 0)
            total = usdt.get('total', 0)
            logger.info(f"Balance: ${total:.2f} USDT (Free: ${free:.2f})")
            return free
        except Exception as e:
            logger.error(f"Error fetching balance: {str(e)}")
            return 0
    
    def analyze_pair(self, symbol):
        """Technical analysis"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, '4h', limit=50)
            if len(ohlcv) < 30:
                return None
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            closes = df['close'].values
            highs = df['high'].values
            lows = df['low'].values
            
            # Indicators
            rsi = talib.RSI(closes, timeperiod=14)[-1]
            macd, macdsignal, macdhist = talib.MACD(closes)
            upper, middle, lower = talib.BBANDS(closes, timeperiod=20)
            ema_9 = talib.EMA(closes, timeperiod=9)[-1]
            ema_21 = talib.EMA(closes, timeperiod=21)[-1]
            
            current_price = closes[-1]
            bb_position = (current_price - lower[-1]) / (upper[-1] - lower[-1])
            
            # Signal logic
            signal = self.calculate_signal(
                current_price, rsi, macd[-1], macdsignal[-1], macdhist[-1],
                bb_position, ema_9, ema_21
            )
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'rsi': rsi,
                'macd': macd[-1],
                'macd_signal': macdsignal[-1],
                'bb_position': bb_position,
                'signal': signal['action'],
                'confidence': signal['confidence'],
                'entry': signal.get('entry'),
                'stop_loss': signal.get('stop_loss'),
                'take_profit': signal.get('take_profit')
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {str(e)}")
            return None
    
    def calculate_signal(self, price, rsi, macd, macd_sig, macd_hist, bb_pos, ema9, ema21):
        """Calculate trading signal"""
        score = 0
        
        if rsi < 30:
            score += 25
        elif rsi > 70:
            score -= 25
        
        if macd > macd_sig and macd_hist > 0:
            score += 25
        elif macd < macd_sig and macd_hist < 0:
            score -= 25
        
        if bb_pos < 0.2:
            score += 20
        elif bb_pos > 0.8:
            score -= 20
        
        if ema9 > ema21:
            score += 15
        else:
            score -= 15
        
        if score >= 40:  # AGGRESSIVE: Lowered from 60
            entry = price
            stop_loss = entry * (1 - self.stop_loss_pct)
            take_profit = entry * (1 + self.take_profit_pct)
            return {
                'action': 'BUY',
                'confidence': min(score, 90),
                'entry': entry,
                'stop_loss': stop_loss,
                'take_profit': take_profit
            }
        elif score <= -25:  # AGGRESSIVE: Lowered from -40
            return {'action': 'SELL', 'confidence': min(abs(score), 90)}
        
        return {'action': 'HOLD', 'confidence': 0}
    
    def find_best_trade(self):
        """Find best opportunity"""
        opportunities = []
        for pair in self.pairs:
            analysis = self.analyze_pair(pair)
            if analysis and analysis['signal'] == 'BUY':
                opportunities.append(analysis)
        
        if not opportunities:
            return None
        
        opportunities.sort(key=lambda x: x['confidence'], reverse=True)
        return opportunities[0]
    
    def calculate_position_size(self, entry_price):
        """Calculate position size with minimum enforcement"""
        balance = self.get_balance()
        if balance < 25:  # Need at least $25
            return 0
        
        # Calculate position value (max 20% of balance or max_position_size)
        position_value = min(self.max_position_size, balance * 0.20)
        
        # Ensure minimum $25 position
        position_value = max(position_value, 25.0)
        
        amount = position_value / entry_price
        
        # Round up to ensure minimum precision
        if entry_price > 1000:  # ETH, BTC
            amount = max(round(amount, 3), 0.015)  # Minimum 0.015 for ETH
        elif entry_price > 100:  # SOL, LINK
            amount = max(round(amount, 2), 0.15)
        else:  # XRP, ADA, DOGE
            amount = max(round(amount, 1), 1.0)
        
        return amount
    
    def open_position(self, symbol, amount, stop_loss, take_profit):
        """Open buy position with native TP/SL"""
        try:
            # Check if position already exists for this symbol
            if symbol in self.positions:
                logger.info(f"Skipping {symbol}: Position already open (Entry: ${self.positions[symbol]['entry']:.4f})")
                return False
            
            # Create market order with TP/SL params
            order = self.exchange.create_order(
                symbol,
                'market',
                'buy',
                amount,
                None,
                {
                    'stopLoss': str(stop_loss),
                    'takeProfit': str(take_profit)
                }
            )
            entry_price = order['price'] if order['price'] else order['average']
            
            self.positions[symbol] = {
                'amount': amount,
                'entry': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'time': datetime.now(),
                'order_id': order['id']
            }
            
            self.total_trades += 1
            
            msg = f"""
[POSITION OPENED - TP/SL SET]
Pair: {symbol}
Entry: ${entry_price:.2f}
Amount: {amount:.6f}
Stop Loss: ${stop_loss:.2f}
Take Profit: ${take_profit:.2f}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            logger.info(msg)
            print(msg)
            
            # Send Telegram notification
            if NOTIFIER_AVAILABLE:
                try:
                    notify_trade_opened(
                        symbol=symbol,
                        side="LONG",
                        amount=amount,
                        entry=entry_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        bot_name="Bybit Trader"
                    )
                except Exception as e:
                    logger.error(f"Failed to send notification: {e}")
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error opening position: {error_msg}")
            # Don't send Telegram alert for balance errors (not actual errors)
            if NOTIFIER_AVAILABLE and "ab not enough" not in error_msg:
                try:
                    notify_error(error_msg, "Bybit Trader")
                except:
                    pass
            return False
    
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
                amount = position['amount']
                
                # Calculate current profit
                current_profit_pct = (current_price - entry) / entry
                unrealized_pnl = (current_price - entry) * amount
                
                logger.info(f"Checking {symbol}: Current=${current_price:.4f}, Entry=${entry:.4f}, "
                          f"TP=${take_profit:.4f}, SL=${stop_loss:.4f}, PnL=${unrealized_pnl:.2f} ({current_profit_pct*100:.2f}%)")
                
                # TRAILING TAKE PROFIT LOGIC
                if self.use_trailing_tp and current_profit_pct > self.trailing_tp_activation:
                    # Trailing activated - move take profit to lock in gains
                    new_tp = current_price * (1 - self.trailing_tp_distance)
                    
                    # Only move TP up, never down
                    if new_tp > take_profit:
                        position['take_profit'] = new_tp
                        logger.info(f"🎯 TRAILING TP UPDATED: {symbol} new TP=${new_tp:.4f} "
                                  f"(locked {current_profit_pct*100:.1f}% profit)")
                        
                        # Send notification when trailing TP activates
                        if NOTIFIER_AVAILABLE:
                            try:
                                notify_trade_opened(
                                    symbol=symbol,
                                    side="LONG",
                                    amount=amount,
                                    entry=entry,
                                    stop_loss=stop_loss,
                                    take_profit=new_tp,
                                    bot_name="🎯 Bybit Trader - Trailing TP"
                                )
                            except:
                                pass
                
                # Check stop loss and take profit with minimum hold time
                # Minimum hold time: 5 minutes (prevent immediate closes)
                hold_time = (datetime.now() - position.get('time', datetime.now())).total_seconds()
                min_hold_time = 300  # 5 minutes
                
                if current_price <= stop_loss:
                    pnl = (current_price - entry) * amount
                    self.close_position(symbol, current_price, 'STOP LOSS', pnl)
                elif current_price >= take_profit and hold_time >= min_hold_time:
                    pnl = (current_price - entry) * amount
                    self.close_position(symbol, current_price, 'TAKE PROFIT', pnl)
                elif current_price >= take_profit and hold_time < min_hold_time:
                    logger.info(f"⏳ {symbol}: TP hit but holding for min time ({hold_time:.0f}s < {min_hold_time}s)")
                    
            except Exception as e:
                logger.error(f"Error checking position {symbol}: {str(e)}")
    
    def close_position(self, symbol, exit_price, reason, pnl):
        """Close position"""
        try:
            position = self.positions[symbol]
            order = self.exchange.create_market_sell_order(symbol, position['amount'])
            
            self.daily_pnl += pnl
            if pnl > 0:
                self.winning_trades += 1
            
            win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
            
            msg = f"""
[POSITION CLOSED]
Pair: {symbol}
Entry: ${position['entry']:.2f}
Exit: ${exit_price:.2f}
PnL: ${pnl:.2f}
Reason: {reason}
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
                        side="LONG",
                        entry=position['entry'],
                        exit_price=exit_price,
                        pnl=pnl,
                        reason=reason,
                        win_rate=win_rate,
                        bot_name="Bybit Trader"
                    )
                except Exception as e:
                    logger.error(f"Failed to send notification: {e}")
            
            del self.positions[symbol]
            
        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
            if NOTIFIER_AVAILABLE:
                try:
                    notify_error(str(e), "Bybit Trader")
                except:
                    pass
    
    def scan_and_trade(self):
        """Main trading loop"""
        logger.info("Scanning markets for opportunities...")
        
        # Check existing positions
        self.check_positions()
        
        # Don't open new if at max
        if len(self.positions) >= self.max_open_positions:
            logger.info(f"Max positions reached ({self.max_open_positions})")
            return
        
        # Check balance
        balance = self.get_balance()
        if balance < 10:
            logger.warning("Low balance - waiting for more funds")
            return
        
        # Find opportunity
        opportunity = self.find_best_trade()
        
        if opportunity:
            symbol = opportunity['symbol']
            
            if symbol in self.positions:
                logger.info(f"Already in position for {symbol}")
                return
            
            amount = self.calculate_position_size(opportunity['entry'])
            
            if amount > 0:
                logger.info(f"Found opportunity: {opportunity}")
                self.open_position(
                    symbol,
                    amount,
                    opportunity['stop_loss'],
                    opportunity['take_profit']
                )
        else:
            logger.info("No high-confidence opportunities found. Holding.")
    
    def run(self):
        """Main loop"""
        logger.info("="*60)
        logger.info("BYBIT PROFESSIONAL TRADER STARTED")
        logger.info(f"Initial Balance: ${self.initial_balance}")
        logger.info(f"Trading Pairs: {', '.join(self.pairs)}")
        logger.info("="*60)
        
        balance = self.get_balance()
        
        while True:
            try:
                self.scan_and_trade()
                
                # Status update
                status = f"Balance: ${balance:.2f} | Trades: {self.total_trades} | Win Rate: {(self.winning_trades/self.total_trades*100) if self.total_trades > 0 else 0:.1f}%"
                logger.info(status)
                
                # Wait 2 minutes - AGGRESSIVE SCANNING
                logger.info("Waiting 2 minutes for next scan...")
                time.sleep(120)
                
            except KeyboardInterrupt:
                logger.info("Trading stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                time.sleep(60)

if __name__ == "__main__":
    trader = BybitTrader()
    trader.run()
