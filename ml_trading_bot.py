"""
ML Trading Bot Integration
Uses ML predictions to execute trades
"""

import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime
import json
import os
import sys

# Add parent dir for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml_trading_system import MLTradingSystem

class MLTradingBot:
    def __init__(self, symbol='ETH/USDT:USDT', timeframe='15m'):
        self.symbol = symbol
        self.timeframe = timeframe
        self.ml_system = MLTradingSystem(symbol, timeframe)
        self.exchange = self._init_exchange()
        
        # Trading config
        self.leverage = 3
        self.risk_per_trade = 0.02  # 2% of account
        self.min_confidence = 0.75  # 75% confidence required
        self.prediction_threshold = 0.1  # Signal strength threshold
        
        # Load model if exists
        if os.path.exists('ml_trading_model.h5'):
            self.ml_system.load_model()
            print("ML Model loaded and ready!")
        else:
            print("WARNING: No trained model found. Run training first.")
    
    def _init_exchange(self):
        """Initialize exchange"""
        exchange = ccxt.bybit({
            'apiKey': 'bsK06QDhsagOWwFsXQ',
            'secret': 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa',
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
        exchange.set_sandbox_mode(False)
        return exchange
    
    def get_account_balance(self):
        """Get USDT balance"""
        try:
            balance = self.exchange.fetch_balance()
            return balance['USDT']['free']
        except Exception as e:
            print(f"Error fetching balance: {e}")
            return 0
    
    def get_position(self):
        """Check if position exists"""
        try:
            positions = self.exchange.fetch_positions([self.symbol])
            for pos in positions:
                if pos['symbol'] == self.symbol and abs(float(pos['contracts'])) > 0:
                    return pos
            return None
        except Exception as e:
            print(f"Error fetching position: {e}")
            return None
    
    def calculate_position_size(self, confidence):
        """Calculate position size based on confidence and risk"""
        balance = self.get_account_balance()
        risk_amount = balance * self.risk_per_trade
        
        # Scale position by confidence (higher confidence = larger position)
        position_multiplier = confidence  # 0.75 to 1.0
        position_size = (risk_amount * position_multiplier) / 100  # Convert to contracts
        
        # Max position limit
        max_position = balance * 0.25 / 100  # Max 25% of account
        position_size = min(position_size, max_position)
        
        return max(1, int(position_size))  # Minimum 1 contract
    
    def execute_trade(self, signal, confidence):
        """Execute trade based on ML signal"""
        print(f"\n{'='*60}")
        print(f"ML SIGNAL: {signal} (Confidence: {confidence:.2%})")
        print(f"{'='*60}")
        
        # Check if confidence is high enough
        if confidence < self.min_confidence:
            print(f"Confidence too low ({confidence:.2%} < {self.min_confidence:.2%}). Skipping.")
            return None
        
        # Check existing position
        existing_position = self.get_position()
        
        if existing_position:
            current_side = 'LONG' if existing_position['side'] == 'long' else 'SHORT'
            
            # If signal matches existing position, hold
            if (signal == 'UP' and current_side == 'LONG') or \
               (signal == 'DOWN' and current_side == 'SHORT'):
                print(f"Already in {current_side} position. Holding.")
                return None
            
            # If signal opposite, close and reverse
            print(f"Closing {current_side} position to reverse...")
            self.close_position(existing_position)
            time.sleep(2)
        
        # Calculate position size
        position_size = self.calculate_position_size(confidence)
        
        # Execute trade
        try:
            if signal == 'UP':
                print(f"Opening LONG position: {position_size} contracts")
                order = self.exchange.create_market_buy_order(
                    self.symbol, position_size, {'leverage': self.leverage}
                )
                self.set_stop_loss_take_profit('LONG', position_size)
                
            elif signal == 'DOWN':
                print(f"Opening SHORT position: {position_size} contracts")
                order = self.exchange.create_market_sell_order(
                    self.symbol, position_size, {'leverage': self.leverage}
                )
                self.set_stop_loss_take_profit('SHORT', position_size)
            
            print(f"Order executed: {order['id']}")
            return order
            
        except Exception as e:
            print(f"Error executing trade: {e}")
            return None
    
    def set_stop_loss_take_profit(self, side, position_size):
        """Set TP/SL orders"""
        try:
            # Get current price
            ticker = self.exchange.fetch_ticker(self.symbol)
            current_price = ticker['last']
            
            # Set SL at 1.5%, TP at 3%
            if side == 'LONG':
                sl_price = current_price * 0.985
                tp_price = current_price * 1.03
            else:
                sl_price = current_price * 1.015
                tp_price = current_price * 0.97
            
            # Create stop loss
            self.exchange.create_order(
                self.symbol, 'stop_market', 
                'sell' if side == 'LONG' else 'buy',
                position_size, None, {'stopPrice': sl_price}
            )
            
            # Create take profit
            self.exchange.create_order(
                self.symbol, 'take_profit_market',
                'sell' if side == 'LONG' else 'buy',
                position_size, None, {'stopPrice': tp_price}
            )
            
            print(f"SL set at {sl_price:.2f}, TP set at {tp_price:.2f}")
            
        except Exception as e:
            print(f"Error setting TP/SL: {e}")
    
    def close_position(self, position):
        """Close existing position"""
        try:
            side = 'sell' if position['side'] == 'long' else 'buy'
            size = abs(float(position['contracts']))
            
            self.exchange.create_market_order(self.symbol, side, size)
            print(f"Closed {position['side'].upper()} position")
            
        except Exception as e:
            print(f"Error closing position: {e}")
    
    def run_trading_loop(self, interval_minutes=15):
        """Main trading loop"""
        print(f"\n{'='*60}")
        print("ML TRADING BOT STARTED")
        print(f"Symbol: {self.symbol}, Timeframe: {self.timeframe}")
        print(f"Min Confidence: {self.min_confidence:.0%}")
        print(f"{'='*60}\n")
        
        while True:
            try:
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scanning...")
                
                # Fetch recent data for prediction
                ohlcv = self.exchange.fetch_ohlcv(
                    self.symbol, self.timeframe, limit=100
                )
                
                df = pd.DataFrame(
                    ohlcv,
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                
                # Get ML prediction
                prediction = self.ml_system.predict(df)
                
                print(f"Prediction: {prediction['prediction']}")
                print(f"Confidence: {prediction['confidence']:.2%}")
                print(f"Probabilities: UP={prediction['probabilities']['up']:.2%}, "
                      f"DOWN={prediction['probabilities']['down']:.2%}")
                
                # Execute if strong signal
                if prediction['prediction'] in ['UP', 'DOWN']:
                    self.execute_trade(
                        prediction['prediction'],
                        prediction['confidence']
                    )
                else:
                    print("Signal: NEUTRAL - No action")
                
                # Wait for next candle
                print(f"Waiting {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
                
            except Exception as e:
                print(f"Error in trading loop: {e}")
                time.sleep(60)  # Wait 1 minute on error


if __name__ == "__main__":
    # Create and run ML trading bot
    bot = MLTradingBot(symbol='ETH/USDT:USDT', timeframe='15m')
    
    # To train first:
    # bot.ml_system.train(epochs=50)
    
    # To run live trading:
    # bot.run_trading_loop(interval_minutes=15)
    
    print("\nML Trading Bot Ready!")
    print("1. Run: bot.ml_system.train(epochs=50) to train model")
    print("2. Run: bot.run_trading_loop() to start live trading")
