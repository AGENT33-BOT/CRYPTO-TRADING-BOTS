"""
Lightweight ML Training - Reduced Memory
"""

import ccxt
import pandas as pd
import numpy as np
import talib
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier
import pickle
import warnings
warnings.filterwarnings('ignore')

def train_lightweight_model(symbol='ETH/USDT:USDT'):
    """Train lightweight model using Random Forest (less memory than LSTM)"""
    
    print(f"\nTraining model for {symbol}...")
    
    # Init exchange
    exchange = ccxt.bybit({
        'apiKey': 'bsK06QDhsagOWwFsXQ',
        'secret': 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa',
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })
    exchange.set_sandbox_mode(False)
    
    # Fetch data
    print("  Fetching historical data...")
    ohlcv = exchange.fetch_ohlcv(symbol, '15m', limit=3000)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    # Features
    print("  Creating features...")
    df['returns'] = df['close'].pct_change()
    df['rsi'] = talib.RSI(df['close'].values, timeperiod=14)
    df['macd'], _, _ = talib.MACD(df['close'].values)
    df['ema_20'] = talib.EMA(df['close'].values, timeperiod=20)
    df['ema_50'] = talib.EMA(df['close'].values, timeperiod=50)
    
    # Target: 1 if price up in next 3 candles, 0 if down
    df['future_return'] = df['close'].shift(-3) / df['close'] - 1
    df['target'] = np.where(df['future_return'] > 0.005, 1, 0)
    
    df.dropna(inplace=True)
    
    # Prepare features
    feature_cols = ['returns', 'rsi', 'macd', 'volume']
    X = df[feature_cols].values
    y = df['target'].values
    
    # Scale
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train model
    print("  Training Random Forest...")
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_scaled, y)
    
    # Accuracy
    accuracy = model.score(X_scaled, y)
    print(f"  Training accuracy: {accuracy:.2%}")
    
    # Save
    safe_symbol = symbol.replace('/', '_')
    with open(f'rf_model_{safe_symbol}.pkl', 'wb') as f:
        pickle.dump(model, f)
    with open(f'rf_scaler_{safe_symbol}.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    with open(f'rf_features_{safe_symbol}.txt', 'w') as f:
        f.write('\n'.join(feature_cols))
    
    print(f"  ✓ Model saved for {symbol}")
    return True

# Train for all symbols
symbols = ['ETH/USDT:USDT', 'NEAR/USDT:USDT', 'DOGE/USDT:USDT']

print("="*60)
print("TRAINING LIGHTWEIGHT ML MODELS")
print("="*60)

for symbol in symbols:
    try:
        train_lightweight_model(symbol)
    except Exception as e:
        print(f"  Error with {symbol}: {e}")

print("\n" + "="*60)
print("TRAINING COMPLETE")
print("="*60)
