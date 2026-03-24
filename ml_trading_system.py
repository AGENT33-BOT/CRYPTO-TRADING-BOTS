"""
ML Trading System for Bybit
Neural Network-based price prediction and trade execution
"""

import ccxt
import pandas as pd
import numpy as np
import talib
from datetime import datetime, timedelta
import json
import os
import pickle
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import warnings
warnings.filterwarnings('ignore')

# Set random seeds for reproducibility
np.random.seed(42)
tf.random.set_seed(42)

class MLTradingSystem:
    def __init__(self, symbol='ETH/USDT:USDT', timeframe='15m'):
        self.symbol = symbol
        self.timeframe = timeframe
        self.exchange = self._init_exchange()
        self.scaler = MinMaxScaler()
        self.model = None
        self.sequence_length = 60  # 60 candles lookback
        self.prediction_horizon = 3  # Predict 3 candles ahead
        self.features = []
        
    def _init_exchange(self):
        """Initialize Bybit exchange"""
        exchange = ccxt.bybit({
            'apiKey': 'bsK06QDhsagOWwFsXQ',
            'secret': 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa',
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
        exchange.set_sandbox_mode(False)
        return exchange
    
    def fetch_historical_data(self, limit=5000):
        """Fetch historical OHLCV data"""
        print(f"Fetching {limit} candles of historical data...")
        
        try:
            ohlcv = self.exchange.fetch_ohlcv(
                self.symbol, 
                timeframe=self.timeframe, 
                limit=limit
            )
            
            df = pd.DataFrame(
                ohlcv, 
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            print(f"Loaded {len(df)} candles")
            return df
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None
    
    def engineer_features(self, df):
        """Create technical indicator features for ML"""
        print("Engineering features...")
        
        # Price-based features
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Moving averages
        for period in [7, 14, 21, 50]:
            df[f'ma_{period}'] = df['close'].rolling(window=period).mean()
            df[f'ema_{period}'] = talib.EMA(df['close'].values, timeperiod=period)
            df[f'ma_ratio_{period}'] = df['close'] / df[f'ma_{period}']
        
        # RSI
        df['rsi_14'] = talib.RSI(df['close'].values, timeperiod=14)
        df['rsi_7'] = talib.RSI(df['close'].values, timeperiod=7)
        
        # MACD
        macd, macd_signal, macd_hist = talib.MACD(
            df['close'].values, 
            fastperiod=12, 
            slowperiod=26, 
            signalperiod=9
        )
        df['macd'] = macd
        df['macd_signal'] = macd_signal
        df['macd_hist'] = macd_hist
        
        # Bollinger Bands
        upper, middle, lower = talib.BBANDS(
            df['close'].values, 
            timeperiod=20, 
            nbdevup=2, 
            nbdevdn=2
        )
        df['bb_upper'] = upper
        df['bb_middle'] = middle
        df['bb_lower'] = lower
        df['bb_position'] = (df['close'] - lower) / (upper - lower)
        df['bb_width'] = (upper - lower) / middle
        
        # Volume indicators
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        # Volatility
        df['atr'] = talib.ATR(df['high'].values, df['low'].values, df['close'].values, timeperiod=14)
        df['atr_ratio'] = df['atr'] / df['close']
        
        # Price action
        df['body'] = df['close'] - df['open']
        df['body_pct'] = abs(df['body']) / (df['high'] - df['low'] + 0.0001)
        df['upper_shadow'] = df['high'] - df[['open', 'close']].max(axis=1)
        df['lower_shadow'] = df[['open', 'close']].min(axis=1) - df['low']
        
        # Trend features
        df['trend'] = np.where(df['close'] > df['close'].shift(1), 1, 0)
        df['trend_3'] = df['trend'].rolling(window=3).sum()
        
        # Target variable: Future returns
        df['future_returns'] = df['close'].shift(-self.prediction_horizon) / df['close'] - 1
        df['target'] = np.where(df['future_returns'] > 0.005, 2,  # Strong up
                               np.where(df['future_returns'] < -0.005, 0, 1))  # Strong down, neutral
        
        # Drop NaN values
        df.dropna(inplace=True)
        
        # Select feature columns
        feature_cols = [col for col in df.columns if col not in 
                       ['open', 'high', 'low', 'close', 'volume', 'future_returns', 'target']]
        
        self.features = feature_cols
        print(f"Created {len(feature_cols)} features")
        print(f"Target distribution: {df['target'].value_counts().to_dict()}")
        
        return df
    
    def prepare_sequences(self, df):
        """Prepare LSTM sequences"""
        print("Preparing sequences...")
        
        X = df[self.features].values
        y = df['target'].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Create sequences
        X_seq = []
        y_seq = []
        
        for i in range(len(X_scaled) - self.sequence_length):
            X_seq.append(X_scaled[i:i+self.sequence_length])
            y_seq.append(y[i+self.sequence_length])
        
        X_seq = np.array(X_seq)
        y_seq = np.array(y_seq)
        
        # One-hot encode targets
        y_seq = tf.keras.utils.to_categorical(y_seq, num_classes=3)
        
        print(f"Sequences shape: X={X_seq.shape}, y={y_seq.shape}")
        
        return X_seq, y_seq
    
    def build_model(self, input_shape):
        """Build LSTM neural network"""
        print("Building LSTM model...")
        
        model = Sequential([
            LSTM(128, return_sequences=True, input_shape=input_shape),
            BatchNormalization(),
            Dropout(0.3),
            
            LSTM(64, return_sequences=True),
            BatchNormalization(),
            Dropout(0.3),
            
            LSTM(32, return_sequences=False),
            BatchNormalization(),
            Dropout(0.3),
            
            Dense(64, activation='relu'),
            BatchNormalization(),
            Dropout(0.3),
            
            Dense(32, activation='relu'),
            Dense(3, activation='softmax')  # 3 classes: down, neutral, up
        ])
        
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        print(model.summary())
        return model
    
    def train(self, epochs=100, batch_size=32):
        """Train the ML model"""
        print("="*60)
        print("TRAINING ML TRADING MODEL")
        print("="*60)
        
        # Fetch and prepare data
        df = self.fetch_historical_data()
        if df is None or len(df) < 1000:
            print("Not enough data for training")
            return False
        
        df = self.engineer_features(df)
        X, y = self.prepare_sequences(df)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False  # Time series - don't shuffle
        )
        
        print(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
        
        # Build model
        self.model = self.build_model((X.shape[1], X.shape[2]))
        
        # Callbacks
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
            ModelCheckpoint('ml_trading_model.h5', save_best_only=True)
        ]
        
        # Train
        print("\nTraining...")
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2,
            callbacks=callbacks,
            verbose=1
        )
        
        # Evaluate
        print("\nEvaluating...")
        loss, accuracy = self.model.evaluate(X_test, y_test, verbose=0)
        print(f"Test Loss: {loss:.4f}, Test Accuracy: {accuracy:.4f}")
        
        # Save model and scaler
        self.save_model()
        
        return True
    
    def predict(self, recent_data):
        """Make prediction on recent data"""
        if self.model is None:
            self.load_model()
        
        # Engineer features
        df = self.engineer_features(recent_data)
        
        # Get last sequence
        X = df[self.features].values[-self.sequence_length:]
        X_scaled = self.scaler.transform(X)
        X_seq = np.array([X_scaled])
        
        # Predict
        prediction = self.model.predict(X_seq, verbose=0)
        
        # Interpret
        class_names = ['DOWN', 'NEUTRAL', 'UP']
        predicted_class = np.argmax(prediction[0])
        confidence = prediction[0][predicted_class]
        
        return {
            'prediction': class_names[predicted_class],
            'confidence': float(confidence),
            'probabilities': {
                'down': float(prediction[0][0]),
                'neutral': float(prediction[0][1]),
                'up': float(prediction[0][2])
            }
        }
    
    def save_model(self):
        """Save model and scaler"""
        self.model.save('ml_trading_model.h5')
        with open('ml_scaler.pkl', 'wb') as f:
            pickle.dump(self.scaler, f)
        with open('ml_features.json', 'w') as f:
            json.dump(self.features, f)
        print("\nModel saved!")
    
    def load_model(self):
        """Load model and scaler"""
        self.model = load_model('ml_trading_model.h5')
        with open('ml_scaler.pkl', 'rb') as f:
            self.scaler = pickle.load(f)
        with open('ml_features.json', 'r') as f:
            self.features = json.load(f)
        print("Model loaded!")


if __name__ == "__main__":
    # Example usage
    ml_system = MLTradingSystem(symbol='ETH/USDT:USDT', timeframe='15m')
    
    # Train model
    # ml_system.train(epochs=50)
    
    print("\nML Trading System Ready!")
    print("Run ml_system.train() to train on historical data")
    print("Run ml_system.predict(recent_data) to get trading signals")
