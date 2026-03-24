"""
Train ML Models for Multiple Symbols
ETH, NEAR, DOGE
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml_trading_system import MLTradingSystem

symbols = [
    ('ETH/USDT:USDT', '15m'),
    ('NEAR/USDT:USDT', '15m'),
    ('DOGE/USDT:USDT', '15m')
]

print("="*70)
print("TRAINING ML MODELS FOR MULTIPLE SYMBOLS")
print("="*70)

for symbol, timeframe in symbols:
    print(f"\n\n{'='*70}")
    print(f"TRAINING: {symbol}")
    print(f"{'='*70}")
    
    try:
        ml_system = MLTradingSystem(symbol=symbol, timeframe=timeframe)
        success = ml_system.train(epochs=30, batch_size=32)  # Reduced epochs for speed
        
        if success:
            print(f"\n✓ {symbol} model trained successfully!")
            # Save with symbol-specific name
            import shutil
            if os.path.exists('ml_trading_model.h5'):
                shutil.copy('ml_trading_model.h5', f'ml_model_{symbol.replace("/", "_")}.h5')
                shutil.copy('ml_scaler.pkl', f'ml_scaler_{symbol.replace("/", "_")}.pkl')
        else:
            print(f"\n✗ {symbol} training failed")
            
    except Exception as e:
        print(f"\n✗ Error training {symbol}: {e}")

print("\n" + "="*70)
print("ALL TRAINING COMPLETE")
print("="*70)
