"""
Live ML Trading Bot v2 - Uses Trained Random Forest Models
Fixed: 20% position sizing
"""

import ccxt
import pandas as pd
import numpy as np
import talib
import pickle
import time
from datetime import datetime
import os
import sys

# Import Telegram reporter
try:
    from telegram_reporter import TelegramReporter
except:
    TelegramReporter = None

class LiveMLTrader:
    def __init__(self, symbol='ETH/USDT:USDT'):
        self.symbol = symbol
        self.exchange = self._init_exchange()
        self.model = None
        self.scaler = None
        self.features = None
        self.load_model()
        
        # Trading config - FIXED: 20% position size
        self.leverage = 3
        self.risk_per_trade = 0.20  # 20% of available balance
        self.min_confidence = 0.65
        
        # Telegram
        self.telegram = None
        self._init_telegram()
        
    def _init_exchange(self):
        exchange = ccxt.bybit({
            'apiKey': 'bsK06QDhsagOWwFsXQ',
            'secret': 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa',
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
        exchange.set_sandbox_mode(False)
        return exchange
    
    def _init_telegram(self):
        try:
            if TelegramReporter:
                BOT_TOKEN = "8586893914:AAEIuNFlGNbhDeUQ-eXUOmTm0KHw_-aOtuI"
                CHAT_ID = "5804173449"
                self.telegram = TelegramReporter(BOT_TOKEN, chat_id=CHAT_ID)
        except:
            self.telegram = None
    
    def load_model(self):
        safe_symbol = self.symbol.replace('/', '_')
        model_file = f'rf_model_{safe_symbol}.pkl'
        scaler_file = f'rf_scaler_{safe_symbol}.pkl'
        features_file = f'rf_features_{safe_symbol}.txt'
        
        if os.path.exists(model_file):
            with open(model_file, 'rb') as f:
                self.model = pickle.load(f)
            with open(scaler_file, 'rb') as f:
                self.scaler = pickle.load(f)
            with open(features_file, 'r') as f:
                self.features = f.read().strip().split('\n')
            print(f"Model loaded for {self.symbol}")
    
    def get_balance(self):
        try:
            balance = self.exchange.fetch_balance()
            return balance['USDT']['free']
        except:
            return 0
    
    def get_position(self):
        try:
            positions = self.exchange.fetch_positions([self.symbol])
            for pos in positions:
                if pos['symbol'] == self.symbol and abs(float(pos['contracts'])) > 0:
                    return pos
            return None
        except:
            return None
    
    def get_prediction(self):
        if not self.model:
            return None
        
        try:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, '15m', limit=50)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            df['returns'] = df['close'].pct_change()
            df['rsi'] = talib.RSI(df['close'].values, timeperiod=14)
            df['macd'], _, _ = talib.MACD(df['close'].values)
            
            latest = df[self.features].iloc[-1].values.reshape(1, -1)
            latest_scaled = self.scaler.transform(latest)
            
            prediction = self.model.predict(latest_scaled)[0]
            probabilities = self.model.predict_proba(latest_scaled)[0]
            confidence = max(probabilities)
            
            return {
                'signal': 'UP' if prediction == 1 else 'DOWN',
                'confidence': confidence,
                'prob_up': probabilities[1],
                'prob_down': probabilities[0]
            }
        except:
            return None
    
    def calculate_position_size(self, confidence):
        """Calculate position size - 20% of balance with minimum checks"""
        balance = self.get_balance()
        
        # Target: 20% of balance
        target_usd = balance * self.risk_per_trade  # 20%
        
        # But must also meet minimum order size
        try:
            ticker = self.exchange.fetch_ticker(self.symbol)
            price = ticker['last']
            
            # Bybit minimums (in contracts)
            if 'ETH' in self.symbol:
                min_contracts = 1      # 0.01 ETH
                usd_per_contract = price * 0.01
                min_usd = 35  # ~$35 minimum
            elif 'NEAR' in self.symbol:
                min_contracts = 10     # 10 NEAR
                usd_per_contract = price * 10
                min_usd = 10  # ~$10 minimum
            elif 'DOGE' in self.symbol:
                min_contracts = 100    # 100 DOGE
                usd_per_contract = price * 100
                min_usd = 8   # ~$8 minimum
            else:
                min_contracts = 1
                usd_per_contract = 1
                min_usd = 10
            
            # Use the LARGER of: 20% target OR minimum required
            actual_usd = max(target_usd, min_usd)
            
            # Scale by confidence (optional, keeps it at least minimum)
            actual_usd = actual_usd * max(confidence, 0.8)
            
            contracts = int(actual_usd / usd_per_contract)
            contracts = max(contracts, min_contracts)
            
            print(f"  Target 20%: ${target_usd:.2f}")
            print(f"  Min required: ${min_usd:.2f}")
            print(f"  Using: ${actual_usd:.2f}")
            print(f"  Contracts: {contracts}")
            
            return contracts
            
        except Exception as e:
            print(f"  Size calc error: {e}")
            return 1
    
    def execute_trade(self, signal, confidence):
        if confidence < self.min_confidence:
            print(f"Confidence too low: {confidence:.2%}")
            return None
        
        existing = self.get_position()
        if existing:
            side = 'LONG' if existing['side'] == 'long' else 'SHORT'
            if (signal == 'UP' and side == 'LONG') or (signal == 'DOWN' and side == 'SHORT'):
                print(f"Already in {side} position")
                return None
            self.close_position(existing)
            time.sleep(2)
        
        position_size = self.calculate_position_size(confidence)
        
        try:
            action = "BUY" if signal == "UP" else "SELL"
            
            if signal == 'UP':
                print(f"Opening LONG: {position_size} contracts")
                order = self.exchange.create_market_buy_order(self.symbol, position_size)
            else:
                print(f"Opening SHORT: {position_size} contracts")
                order = self.exchange.create_market_sell_order(self.symbol, position_size)
            
            if self.telegram:
                ticker = self.exchange.fetch_ticker(self.symbol)
                self.telegram.send_trade_alert(self.symbol, action, ticker['last'], position_size, confidence)
            
            return order
            
        except Exception as e:
            print(f"Error: {e}")
            if self.telegram:
                self.telegram.send_error_alert(self.symbol, str(e))
            return None
    
    def close_position(self, pos):
        try:
            side = 'sell' if pos['side'] == 'long' else 'buy'
            size = abs(float(pos['contracts']))
            self.exchange.create_market_order(self.symbol, side, size)
        except Exception as e:
            print(f"Close error: {e}")
    
    def run(self, interval_minutes=15):
        print(f"\n{'='*60}")
        print(f"ML TRADER v2: {self.symbol}")
        print(f"Position Size: 20% of balance")
        print(f"Risk per Trade: {self.risk_per_trade:.0%}")
        print(f"{'='*60}\n")
        
        if self.telegram:
            self.telegram.send_message(f"🤖 ML Trader Started: {self.symbol} (20% size)")
        
        while True:
            try:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Scanning {self.symbol}...")
                
                pred = self.get_prediction()
                if pred:
                    print(f"Signal: {pred['signal']} | Confidence: {pred['confidence']:.2%}")
                    
                    if pred['confidence'] >= self.min_confidence:
                        self.execute_trade(pred['signal'], pred['confidence'])
                    else:
                        print("Confidence too low, no trade")
                
                print(f"Sleeping {interval_minutes} min...\n")
                time.sleep(interval_minutes * 60)
                
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(60)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', default='ETH/USDT:USDT')
    args = parser.parse_args()
    
    trader = LiveMLTrader(symbol=args.symbol)
    trader.run()
