# AI Crypto Trading System - Autonomous Trader
# Account: $75 initial balance
# Exchange: BTCC
# Risk Level: Conservative (preserving capital priority)

import ccxt
import pandas as pd
import numpy as np
import talib
import requests
import json
import time
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple

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

class AITrader:
    def __init__(self, api_key: str, api_secret: str, passphrase: str = None):
        """Initialize BTCC exchange connection"""
        self.exchange = ccxt.btcc({
            'apiKey': api_key,
            'secret': api_secret,
            'password': passphrase,
            'enableRateLimit': True,
        })
        
        # Trading Parameters for $75 account
        self.initial_balance = 75.0
        self.max_position_size = 15.0  # Max $15 per trade (20% of account)
        self.max_daily_loss = 10.0     # Stop trading after $10 loss
        self.max_open_positions = 2    # Max 2 positions at once
        self.stop_loss_pct = 0.05      # 5% stop loss
        self.take_profit_pct = 0.10    # 10% take profit
        self.min_risk_reward = 1.5     # Only trades with 1.5:1 RR
        
        # Trading pairs to analyze
        self.pairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'ADA/USDT']
        
        # Track performance
        self.daily_pnl = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.positions = {}
        self.trading_enabled = True
        
        logger.info(f"AI Trader initialized with ${self.initial_balance} balance")
    
    def analyze_market(self, symbol: str, timeframe: str = '1h') -> Dict:
        """Analyze a trading pair and return signals"""
        try:
            # Fetch OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Technical Indicators
            # RSI (14 periods)
            df['rsi'] = talib.RSI(df['close'], timeperiod=14)
            
            # MACD
            macd, macdsignal, macdhist = talib.MACD(df['close'])
            df['macd'] = macd
            df['macdsignal'] = macdsignal
            df['macdhist'] = macdhist
            
            # Bollinger Bands
            upper, middle, lower = talib.BBANDS(df['close'])
            df['bb_upper'] = upper
            df['bb_middle'] = middle
            df['bb_lower'] = lower
            
            # Moving Averages
            df['sma_20'] = talib.SMA(df['close'], timeperiod=20)
            df['sma_50'] = talib.SMA(df['close'], timeperiod=50)
            df['ema_12'] = talib.EMA(df['close'], timeperiod=12)
            df['ema_26'] = talib.EMA(df['close'], timeperiod=26)
            
            # ATR for volatility
            df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
            
            # Get latest values
            current = df.iloc[-1]
            previous = df.iloc[-2]
            
            # Calculate signals
            signal = self._calculate_signal(df, current, previous)
            
            return {
                'symbol': symbol,
                'current_price': current['close'],
                'rsi': current['rsi'],
                'macd': current['macd'],
                'macd_signal': current['macdsignal'],
                'bb_position': (current['close'] - current['bb_lower']) / (current['bb_upper'] - current['bb_lower']),
                'trend': 'bullish' if current['sma_20'] > current['sma_50'] else 'bearish',
                'volatility': current['atr'] / current['close'] * 100,  # ATR as % of price
                'signal': signal['action'],
                'confidence': signal['confidence'],
                'entry_price': signal.get('entry'),
                'stop_loss': signal.get('stop_loss'),
                'take_profit': signal.get('take_profit'),
                'risk_reward': signal.get('risk_reward')
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {str(e)}")
            return None
    
    def _calculate_signal(self, df: pd.DataFrame, current, previous) -> Dict:
        """Calculate trading signal based on indicators"""
        signal = {'action': 'HOLD', 'confidence': 0}
        
        # RSI conditions
        rsi_oversold = current['rsi'] < 30
        rsi_overbought = current['rsi'] > 70
        
        # MACD conditions
        macd_bullish = current['macd'] > current['macdsignal'] and previous['macd'] <= previous['macdsignal']
        macd_bearish = current['macd'] < current['macdsignal'] and previous['macd'] >= previous['macdsignal']
        
        # Bollinger Bands
        price_near_lower = current['close'] < current['bb_lower'] * 1.02  # Within 2% of lower band
        price_near_upper = current['close'] > current['bb_upper'] * 0.98  # Within 2% of upper band
        
        # Trend
        bullish_trend = current['sma_20'] > current['sma_50']
        
        # BUY Signal
        if rsi_oversold and macd_bullish and bullish_trend:
            entry = current['close']
            stop_loss = entry * (1 - self.stop_loss_pct)
            take_profit = entry * (1 + self.take_profit_pct)
            risk = entry - stop_loss
            reward = take_profit - entry
            risk_reward = reward / risk if risk > 0 else 0
            
            if risk_reward >= self.min_risk_reward:
                signal = {
                    'action': 'BUY',
                    'confidence': 80,
                    'entry': entry,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'risk_reward': risk_reward
                }
        
        # SELL Signal (for closing position)
        elif rsi_overbought or macd_bearish:
            signal = {'action': 'SELL', 'confidence': 70}
        
        return signal
    
    def find_best_opportunity(self) -> Optional[Dict]:
        """Scan all pairs and find the best trading opportunity"""
        opportunities = []
        
        for pair in self.pairs:
            analysis = self.analyze_market(pair)
            if analysis and analysis['signal'] == 'BUY':
                opportunities.append(analysis)
        
        if not opportunities:
            return None
        
        # Sort by confidence and risk/reward ratio
        opportunities.sort(key=lambda x: (x['confidence'], x['risk_reward']), reverse=True)
        return opportunities[0]
    
    def calculate_position_size(self, entry_price: float, stop_loss: float) -> float:
        """Calculate position size based on risk"""
        risk_per_trade = 3.0  # Risk $3 per trade (4% of $75)
        risk_per_unit = entry_price - stop_loss
        
        if risk_per_unit <= 0:
            return 0
        
        position_size = risk_per_trade / risk_per_unit
        max_position = self.max_position_size / entry_price
        
        return min(position_size, max_position)
    
    def open_position(self, symbol: str, side: str, amount: float, 
                     stop_loss: float = None, take_profit: float = None) -> bool:
        """Open a new position"""
        try:
            if not self.trading_enabled:
                logger.warning("Trading disabled - daily loss limit reached")
                return False
            
            if len(self.positions) >= self.max_open_positions:
                logger.warning(f"Max positions reached ({self.max_open_positions})")
                return False
            
            # Place market order
            order = self.exchange.create_market_buy_order(symbol, amount) if side == 'buy' \
                    else self.exchange.create_market_sell_order(symbol, amount)
            
            # Record position
            self.positions[symbol] = {
                'side': side,
                'entry_price': order['price'],
                'amount': amount,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'open_time': datetime.now(),
                'order_id': order['id']
            }
            
            self.total_trades += 1
            
            logger.info(f"Opened {side} position: {symbol} @ {order['price']}, Amount: {amount}")
            self._notify(f"🟢 OPENED {side.upper()}\n"
                        f"Pair: {symbol}\n"
                        f"Price: ${order['price']:.2f}\n"
                        f"Amount: {amount:.4f}\n"
                        f"Stop Loss: ${stop_loss:.2f}\n"
                        f"Take Profit: ${take_profit:.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error opening position: {str(e)}")
            return False
    
    def close_position(self, symbol: str, reason: str = 'manual') -> bool:
        """Close an existing position"""
        try:
            if symbol not in self.positions:
                return False
            
            position = self.positions[symbol]
            
            # Close position
            if position['side'] == 'buy':
                order = self.exchange.create_market_sell_order(symbol, position['amount'])
            else:
                order = self.exchange.create_market_buy_order(symbol, position['amount'])
            
            # Calculate PnL
            exit_price = order['price']
            entry_price = position['entry_price']
            pnl = (exit_price - entry_price) * position['amount'] if position['side'] == 'buy' \
                  else (entry_price - exit_price) * position['amount']
            
            self.daily_pnl += pnl
            if pnl > 0:
                self.winning_trades += 1
            
            # Check daily loss limit
            if self.daily_pnl <= -self.max_daily_loss:
                self.trading_enabled = False
                logger.warning("Daily loss limit reached - trading disabled")
            
            logger.info(f"Closed position: {symbol} @ {exit_price}, PnL: ${pnl:.2f}, Reason: {reason}")
            self._notify(f"🔴 CLOSED POSITION\n"
                        f"Pair: {symbol}\n"
                        f"Entry: ${entry_price:.2f}\n"
                        f"Exit: ${exit_price:.2f}\n"
                        f"PnL: ${pnl:.2f} ({pnl/self.initial_balance*100:.1f}%)\n"
                        f"Reason: {reason}")
            
            del self.positions[symbol]
            return True
            
        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
            return False
    
    def check_positions(self):
        """Check open positions for stop loss / take profit triggers"""
        for symbol in list(self.positions.keys()):
            position = self.positions[symbol]
            
            try:
                ticker = self.exchange.fetch_ticker(symbol)
                current_price = ticker['last']
                
                # Check stop loss
                if position['side'] == 'buy' and current_price <= position['stop_loss']:
                    logger.info(f"Stop loss triggered for {symbol} at ${current_price}")
                    self.close_position(symbol, 'stop_loss')
                
                # Check take profit
                elif position['side'] == 'buy' and current_price >= position['take_profit']:
                    logger.info(f"Take profit triggered for {symbol} at ${current_price}")
                    self.close_position(symbol, 'take_profit')
                    
            except Exception as e:
                logger.error(f"Error checking position {symbol}: {str(e)}")
    
    def scan_and_trade(self):
        """Main trading loop - scan for opportunities and trade"""
        logger.info("Starting market scan...")
        
        # Check existing positions first
        self.check_positions()
        
        # Find new opportunity
        opportunity = self.find_best_opportunity()
        
        if opportunity:
            symbol = opportunity['symbol']
            
            # Don't open if already in position
            if symbol in self.positions:
                logger.info(f"Already in position for {symbol}, skipping")
                return
            
            # Calculate position size
            amount = self.calculate_position_size(
                opportunity['entry_price'],
                opportunity['stop_loss']
            )
            
            if amount > 0:
                self.open_position(
                    symbol=symbol,
                    side='buy',
                    amount=amount,
                    stop_loss=opportunity['stop_loss'],
                    take_profit=opportunity['take_profit']
                )
        else:
            logger.info("No trading opportunities found")
    
    def _notify(self, message: str):
        """Send notification (can be implemented for Telegram/email)"""
        print(f"\n{'='*50}\n{message}\n{'='*50}\n")
        # TODO: Add Telegram notification
    
    def get_status(self) -> Dict:
        """Get current trading status"""
        return {
            'balance': self.initial_balance + self.daily_pnl,
            'daily_pnl': self.daily_pnl,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'open_positions': len(self.positions),
            'positions': self.positions,
            'trading_enabled': self.trading_enabled
        }

# Main execution
if __name__ == "__main__":
    # TODO: Add your BTCC API credentials here
    API_KEY = "your_api_key"
    API_SECRET = "your_api_secret"
    PASSPHRASE = "your_passphrase"  # if required
    
    trader = AITrader(API_KEY, API_SECRET, PASSPHRASE)
    
    # Run trading loop
    while True:
        try:
            trader.scan_and_trade()
            status = trader.get_status()
            logger.info(f"Status: {status}")
            
            # Wait 5 minutes between scans
            time.sleep(300)
            
        except KeyboardInterrupt:
            logger.info("Trading stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            time.sleep(60)
