# Bybit Professional Crypto Trader
# Account: $49.95 | VPN: Spain | Auto-Trading Enabled

import ccxt
import pandas as pd
import numpy as np
import talib
import time
from datetime import datetime
import logging
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bybit_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Bybit API Credentials
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
                'options': {
                    'defaultType': 'spot',  # Spot trading
                }
            })
            
            # Load markets
            self.exchange.load_markets()
            logger.info("✅ Connected to Bybit successfully")
            
            # Trading Parameters
            self.initial_balance = 49.95
            self.max_position_size = 12.0  # $12 per trade (24% of account)
            self.max_open_positions = 2
            self.stop_loss_pct = 0.04      # 4% stop loss
            self.take_profit_pct = 0.08    # 8% take profit
            
            # Trading pairs - focus on liquid pairs
            self.pairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT']
            
            # Track state
            self.positions = {}
            self.daily_pnl = 0.0
            self.total_trades = 0
            self.winning_trades = 0
            
        except Exception as e:
            logger.error(f"❌ Failed to connect: {str(e)}")
            raise
    
    def get_balance(self):
        """Get USDT balance"""
        try:
            balance = self.exchange.fetch_balance()
            usdt = balance.get('USDT', {})
            free = usdt.get('free', 0)
            total = usdt.get('total', 0)
            logger.info(f"💰 Balance: ${total:.2f} USDT (Free: ${free:.2f})")
            return free
        except Exception as e:
            logger.error(f"Error fetching balance: {str(e)}")
            return 0
    
    def analyze_pair(self, symbol):
        """Professional technical analysis"""
        try:
            # Get 4h candles for trend analysis
            ohlcv = self.exchange.fetch_ohlcv(symbol, '4h', limit=50)
            
            if len(ohlcv) < 30:
                return None
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            closes = df['close'].values
            highs = df['high'].values
            lows = df['low'].values
            
            # Technical Indicators
            # RSI (14 periods)
            rsi = talib.RSI(closes, timeperiod=14)[-1]
            
            # MACD
            macd, macdsignal, macdhist = talib.MACD(closes)
            macd_val = macd[-1]
            macd_signal = macdsignal[-1]
            macd_hist = macdhist[-1]
            
            # Bollinger Bands
            upper, middle, lower = talib.BBANDS(closes, timeperiod=20)
            bb_position = (closes[-1] - lower[-1]) / (upper[-1] - lower[-1])
            
            # EMAs
            ema_9 = talib.EMA(closes, timeperiod=9)[-1]
            ema_21 = talib.EMA(closes, timeperiod=21)[-1]
            
            # ATR for volatility
            atr = talib.ATR(highs, lows, closes, timeperiod=14)[-1]
            
            # Current price
            current_price = closes[-1]
            
            # Professional Signal Logic
            signal = self._professional_signal(
                current_price, rsi, macd_val, macd_signal, macd_hist,
                bb_position, ema_9, ema_21, atr
            )
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'rsi': rsi,
                'macd': macd_val,
                'macd_signal': macd_signal,
                'macd_hist': macd_hist,
                'bb_position': bb_position,
                'ema_9': ema_9,
                'ema_21': ema_21,
                'atr': atr,
                'signal': signal['action'],
                'confidence': signal['confidence'],
                'entry': signal.get('entry'),
                'stop_loss': signal.get('stop_loss'),
                'take_profit': signal.get('take_profit')
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {str(e)}")
            return None
    
    def _professional_signal(self, price, rsi, macd, macd_sig, macd_hist, 
                            bb_pos, ema9, ema21, atr):
        """Professional trading signal"""
        score = 0
        reasons = []
        
        # RSI Analysis
        if rsi < 30:
            score += 25
            reasons.append("RSI oversold")
        elif rsi > 70:
            score -= 25
            reasons.append("RSI overbought")
        elif 40 < rsi < 60:
            score += 10
            reasons.append("RSI neutral healthy")
        
        # MACD Analysis
        if macd > macd_sig and macd_hist > 0:
            score += 25
            reasons.append("MACD bullish")
        elif macd < macd_sig and macd_hist < 0:
            score -= 25
            reasons.append("MACD bearish")
        
        # Bollinger Bands
        if bb_pos < 0.2:
            score += 20
            reasons.append("Price near lower BB")
        elif bb_pos > 0.8:
            score -= 20
            reasons.append("Price near upper BB")
        
        # EMA Trend
        if ema9 > ema21:
            score += 15
            reasons.append("EMA bullish")
        else:
            score -= 15
            reasons.append("EMA bearish")
        
        # Generate Signal
        if score >= 60:
            entry = price
            stop_loss = entry * (1 - self.stop_loss_pct)
            take_profit = entry * (1 + self.take_profit_pct)
            
            return {
                'action': 'BUY',
                'confidence': min(score, 90),
                'reasons': reasons,
                'entry': entry,
                'stop_loss': stop_loss,
                'take_profit': take_profit
            }
        elif score <= -40:
            return {'action': 'SELL', 'confidence': min(abs(score), 90), 'reasons': reasons}
        
        return {'action': 'HOLD', 'confidence': 0, 'reasons': reasons}
    
    def find_best_trade(self):
        """Find best trading opportunity"""
        opportunities = []
        
        for pair in self.pairs:
            analysis = self.analyze_pair(pair)
            if analysis and analysis['signal'] == 'BUY':
                opportunities.append(analysis)
        
        if not opportunities:
            return None
        
        # Sort by confidence
        opportunities.sort(key=lambda x: x['confidence'], reverse=True)
        return opportunities[0]
    
    def calculate_position_size(self, entry_price):
        """Calculate position size based on account risk"""
        balance = self.get_balance()
        if balance < 10:
            return 0
        
        # Use 20% of available balance per trade
        position_value = min(self.max_position_size, balance * 0.20)
        amount = position_value / entry_price
        
        return amount
    
    def open_position(self, symbol, amount, stop_loss, take_profit):
        """Open a buy position"""
        try:
            order = self.exchange.create_market_buy_order(symbol, amount)
            
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
            
            msg = (f"🟢 POSITION OPENED\n"
                   f"Pair: {symbol}\n"
                   f"Entry: ${entry_price:.2f}\n"
                   f"Amount: {amount:.6f}\n"
                   f"Stop Loss: ${stop_loss:.2f}\n"
                   f"Take Profit: ${take_profit:.2f}")
            
            logger.info(msg)
            print(f"\n{'='*60}\n{msg}\n{'='*60}\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Error opening position: {str(e)}")
            return False
    
    def check_positions(self):
        """Check and close positions if needed"""
        for symbol in list(self.positions.keys()):
            try:
                position = self.positions[symbol]
                ticker = self.exchange.fetch_ticker(symbol)
                current_price = ticker['last']
                
                # Check stop loss
                if current_price <= position['stop_loss']:
                    pnl = (current_price - position['entry']) * position['amount']
                    self.close_position(symbol, current_price, 'STOP LOSS', pnl)
                
                # Check take profit
                elif current_price >= position['take_profit']:
                    pnl = (current_price - position['entry']) * position['amount']
                    self.close_position(symbol, current_price, 'TAKE PROFIT', pnl)
                    
            except Exception as e:
                logger.error(f"Error checking position {symbol}: {str(e)}")
    
    def close_position(self, symbol, exit_price, reason, pnl):
        """Close a position"""
        try:
            position = self.positions[symbol]
            
            order = self.exchange.create_market_sell_order(symbol, position['amount'])
            
            self.daily_pnl += pnl
            if pnl > 0:
                self.winning_trades += 1
            
            win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
            
            msg = (f"🔴 POSITION CLOSED\n"
                   f"Pair: {symbol}\n"
                   f"Entry: ${position['entry']:.2f}\n"
                   f"Exit: ${exit_price:.2f}\n"
                   f"PnL: ${pnl:.2f}\n"
                   f"Reason: {reason}\n"
                   f"Win Rate: {win_rate:.1f}%")
            
            logger.info(msg)
            print(f"\n{'='*60}\n{msg}\n{'='*60}\n")
            
            del self.positions[symbol]
            
        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
    
    def scan_and_trade(self):
        """Main trading loop"""
        logger.info("🔍 Scanning markets for opportunities...")
        
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
                logger.info(f"📊 Analysis: {opportunity}")
                self.open_position(
                    symbol,
                    amount,
                    opportunity['stop_loss'],
                    opportunity['take_profit']
                )
        else:
            logger.info("No high-confidence opportunities found. Holding.")
    
    def run(self):
        """Main trading loop"""
        logger.info("="*60)
        logger.info("🚀 BYBIT PROFESSIONAL TRADER STARTED")
        logger.info(f"💰 Initial Balance: ${self.initial_balance}")
        logger.info(f"📊 Trading Pairs: {', '.join(self.pairs)}")
        logger.info("="*60)
        
        # Initial balance check
        balance = self.get_balance()
        
        while True:
            try:
                self.scan_and_trade()
                
                # Status update
                status = f"💰 Balance: ${balance:.2f} | 📈 Trades: {self.total_trades} | 🎯 Win Rate: {(self.winning_trades/self.total_trades*100) if self.total_trades > 0 else 0:.1f}%"
                logger.info(status)
                
                # Wait 5 minutes between scans
                logger.info("⏳ Waiting 5 minutes for next scan...")
                time.sleep(300)
                
            except KeyboardInterrupt:
                logger.info("🛑 Trading stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                time.sleep(60)

if __name__ == "__main__":
    trader = BybitTrader()
    trader.run()
