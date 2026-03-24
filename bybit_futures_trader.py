# Bybit Futures Trader with 3x LEVERAGE
import ccxt
import pandas as pd
import numpy as np
import talib
import time
from datetime import datetime
import logging

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

# API Credentials
API_KEY = "bsK06QDhsagOWwFsXQ"
API_SECRET = "ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa"

class BybitFuturesTrader:
    def __init__(self):
        """Initialize Bybit Futures connection with 3x leverage"""
        try:
            self.exchange = ccxt.bybit({
                'apiKey': API_KEY,
                'secret': API_SECRET,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',
                    'adjustForTimeDifference': True
                }
            })
            self.exchange.load_markets()
            logger.info("Connected to Bybit Futures successfully")
            
            # LEVERAGE SETTING
            self.leverage = 3
            
            # Trading Parameters
            self.initial_balance = 49.95
            self.max_position_size = 12.0
            self.max_open_positions = 2
            self.stop_loss_pct = 0.04
            self.take_profit_pct = 0.08
            
            # Trading pairs - FUTURES symbols (majors only, TRIA/ZAMA don't have futures yet)
            self.pairs = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'XRP/USDT:USDT']
            
            # Track state
            self.positions = {}
            self.daily_pnl = 0.0
            self.total_trades = 0
            self.winning_trades = 0
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise
    
    def set_leverage(self, symbol):
        """Set leverage for symbol"""
        try:
            self.exchange.set_leverage(self.leverage, symbol)
            logger.info(f"Leverage set to {self.leverage}x for {symbol}")
        except Exception as e:
            logger.info(f"Leverage already set or error: {e}")
    
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
            logger.error(f"Error fetching balance: {e}")
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
            logger.error(f"Error analyzing {symbol}: {e}")
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
        
        if score >= 60:
            entry = price
            stop_loss = entry * (1 - self.stop_loss_pct)
            take_profit = entry * (1 + self.take_profit_pct)
            return {
                'action': 'LONG',
                'confidence': min(score, 90),
                'entry': entry,
                'stop_loss': stop_loss,
                'take_profit': take_profit
            }
        elif score <= -40:
            return {'action': 'SHORT', 'confidence': min(abs(score), 90)}
        
        return {'action': 'HOLD', 'confidence': 0}
    
    def find_best_trade(self):
        """Find best opportunity"""
        opportunities = []
        for pair in self.pairs:
            analysis = self.analyze_pair(pair)
            if analysis and analysis['signal'] == 'LONG':
                opportunities.append(analysis)
        
        if not opportunities:
            return None
        
        opportunities.sort(key=lambda x: x['confidence'], reverse=True)
        return opportunities[0]
    
    def calculate_position_size(self, entry_price):
        """Calculate position size with LEVERAGE"""
        balance = self.get_balance()
        if balance < 10:
            return 0
        
        position_value = min(self.max_position_size, balance * 0.20 * self.leverage)
        amount = position_value / entry_price
        
        return amount
    
    def open_position(self, symbol, side, amount, stop_loss, take_profit):
        """Open futures position"""
        try:
            self.set_leverage(symbol)
            
            if side == 'LONG':
                order = self.exchange.create_market_buy_order(symbol, amount)
            else:
                order = self.exchange.create_market_sell_order(symbol, amount)
            
            entry_price = order['price'] if order['price'] else order['average']
            position_value = amount * entry_price
            margin_used = position_value / self.leverage
            
            self.positions[symbol] = {
                'side': side,
                'amount': amount,
                'entry': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'margin': margin_used,
                'time': datetime.now(),
                'order_id': order['id']
            }
            
            self.total_trades += 1
            
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
                
                if position['side'] == 'LONG':
                    if current_price <= position['stop_loss']:
                        pnl = (current_price - position['entry']) * position['amount']
                        self.close_position(symbol, current_price, 'STOP LOSS', pnl)
                    elif current_price >= position['take_profit']:
                        pnl = (current_price - position['entry']) * position['amount']
                        self.close_position(symbol, current_price, 'TAKE PROFIT', pnl)
                else:
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
            
            self.daily_pnl += pnl
            if pnl > 0:
                self.winning_trades += 1
            
            win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
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
Win Rate: {win_rate:.1f}%
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            logger.info(msg)
            print(msg)
            
            del self.positions[symbol]
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
    
    def scan_and_trade(self):
        """Main trading loop"""
        logger.info("Scanning futures markets for opportunities...")
        
        self.check_positions()
        
        if len(self.positions) >= self.max_open_positions:
            logger.info(f"Max positions reached ({self.max_open_positions})")
            return
        
        balance = self.get_balance()
        if balance < 10:
            logger.warning("Low balance - waiting for more funds")
            return
        
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
                    'LONG',
                    amount,
                    opportunity['stop_loss'],
                    opportunity['take_profit']
                )
        else:
            logger.info("No high-confidence opportunities found. Holding.")
    
    def run(self):
        """Main loop"""
        logger.info("="*60)
        logger.info(f"BYBIT FUTURES TRADER STARTED - {self.leverage}x LEVERAGE")
        logger.info(f"Initial Balance: ${self.initial_balance}")
        logger.info(f"Trading Pairs: {', '.join(self.pairs)}")
        logger.info("="*60)
        
        balance = self.get_balance()
        
        while True:
            try:
                self.scan_and_trade()
                
                status = f"Balance: ${balance:.2f} | Trades: {self.total_trades} | Win Rate: {(self.winning_trades/self.total_trades*100) if self.total_trades > 0 else 0:.1f}%"
                logger.info(status)
                
                logger.info("Waiting 5 minutes for next scan...")
                time.sleep(300)
                
            except KeyboardInterrupt:
                logger.info("Trading stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)

if __name__ == "__main__":
    trader = BybitFuturesTrader()
    trader.run()
