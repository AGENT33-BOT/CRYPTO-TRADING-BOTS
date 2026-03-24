# AI Crypto Trader - CONFIGURED
# Account: $75 | Exchange: BTCC
# AUTO-TRADING ENABLED

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
        logging.FileHandler('trading_log.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API CREDENTIALS
API_KEY = "0c9622dc-3f87-43e4-ac6e-244486c45fb7"
API_SECRET = "08d64f86-682c-4def-849b-ec3b28913d6b"

class AITrader:
    def __init__(self):
        """Initialize BTCC connection"""
        try:
            self.exchange = ccxt.btcc({
                'apiKey': API_KEY,
                'secret': API_SECRET,
                'enableRateLimit': True,
            })
            
            # Verify connection
            self.exchange.load_markets()
            logger.info("✅ Connected to BTCC successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect: {str(e)}")
            raise
        
        # Account Settings
        self.initial_balance = 75.0
        self.max_position_size = 15.0
        self.max_open_positions = 2
        self.stop_loss_pct = 0.05
        self.take_profit_pct = 0.10
        
        # Trading pairs
        self.pairs = ['BTC/USDT', 'ETH/USDT']
        
        # Track state
        self.positions = {}
        self.daily_pnl = 0.0
        self.total_trades = 0
        
        logger.info(f"💰 Target balance: ${self.initial_balance}")
    
    def get_balance(self):
        """Get account balance"""
        try:
            balance = self.exchange.fetch_balance()
            usdt = balance.get('USDT', {})
            free = usdt.get('free', 0)
            total = usdt.get('total', 0)
            logger.info(f"💵 Balance: ${total:.2f} (Free: ${free:.2f})")
            return total
        except Exception as e:
            logger.error(f"Error fetching balance: {str(e)}")
            return 0
    
    def get_price(self, symbol):
        """Get current price"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {str(e)}")
            return None
    
    def analyze_pair(self, symbol):
        """Simple analysis"""
        try:
            # Get OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(symbol, '1h', limit=50)
            
            if len(ohlcv) < 30:
                return None
            
            closes = [x[4] for x in ohlcv]
            
            # Calculate RSI
            rsi = talib.RSI(np.array(closes), timeperiod=14)[-1]
            
            # Current price
            current_price = closes[-1]
            
            # Simple signal
            if rsi < 35:  # Oversold
                return {
                    'symbol': symbol,
                    'price': current_price,
                    'rsi': rsi,
                    'signal': 'BUY',
                    'stop_loss': current_price * 0.95,
                    'take_profit': current_price * 1.10
                }
            elif rsi > 65:  # Overbought
                return {
                    'symbol': symbol,
                    'price': current_price,
                    'rsi': rsi,
                    'signal': 'SELL'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {str(e)}")
            return None
    
    def open_position(self, symbol, amount, stop_loss, take_profit):
        """Open a buy position"""
        try:
            # Create market buy order
            order = self.exchange.create_market_buy_order(symbol, amount)
            
            entry_price = order['price']
            
            self.positions[symbol] = {
                'amount': amount,
                'entry': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'time': datetime.now()
            }
            
            self.total_trades += 1
            
            msg = (f"🟢 POSITION OPENED\n"
                   f"Pair: {symbol}\n"
                   f"Amount: {amount:.6f}\n"
                   f"Entry: ${entry_price:.2f}\n"
                   f"Stop Loss: ${stop_loss:.2f}\n"
                   f"Take Profit: ${take_profit:.2f}")
            
            logger.info(msg)
            print(f"\n{'='*50}\n{msg}\n{'='*50}\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Error opening position: {str(e)}")
            return False
    
    def check_positions(self):
        """Check and close positions if needed"""
        for symbol in list(self.positions.keys()):
            try:
                position = self.positions[symbol]
                current_price = self.get_price(symbol)
                
                if not current_price:
                    continue
                
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
            
            # Create market sell order
            order = self.exchange.create_market_sell_order(symbol, position['amount'])
            
            self.daily_pnl += pnl
            
            msg = (f"🔴 POSITION CLOSED\n"
                   f"Pair: {symbol}\n"
                   f"Exit: ${exit_price:.2f}\n"
                   f"PnL: ${pnl:.2f}\n"
                   f"Reason: {reason}")
            
            logger.info(msg)
            print(f"\n{'='*50}\n{msg}\n{'='*50}\n")
            
            del self.positions[symbol]
            
        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
    
    def scan_and_trade(self):
        """Main trading logic"""
        logger.info("🔍 Scanning markets...")
        
        # Check existing positions
        self.check_positions()
        
        # Don't open new if at max
        if len(self.positions) >= self.max_open_positions:
            logger.info(f"Max positions reached ({self.max_open_positions})")
            return
        
        # Check balance
        balance = self.get_balance()
        if balance < 10:
            logger.warning("Low balance - not trading")
            return
        
        # Find opportunity
        for pair in self.pairs:
            if pair in self.positions:
                continue
            
            analysis = self.analyze_pair(pair)
            
            if analysis and analysis['signal'] == 'BUY':
                # Calculate position size (use 15% of balance)
                position_value = min(self.max_position_size, balance * 0.15)
                amount = position_value / analysis['price']
                
                self.open_position(
                    pair,
                    amount,
                    analysis['stop_loss'],
                    analysis['take_profit']
                )
                break
    
    def run(self):
        """Main loop"""
        logger.info("🚀 Starting AI Trader...")
        
        # Initial balance check
        balance = self.get_balance()
        if balance < 50:
            logger.warning(f"Balance ${balance} is less than expected $75")
        
        while True:
            try:
                self.scan_and_trade()
                
                # Wait 5 minutes
                logger.info("⏳ Waiting 5 minutes...")
                time.sleep(300)
                
            except KeyboardInterrupt:
                logger.info("🛑 Trading stopped")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                time.sleep(60)

# Run if executed directly
if __name__ == "__main__":
    trader = AITrader()
    trader.run()
