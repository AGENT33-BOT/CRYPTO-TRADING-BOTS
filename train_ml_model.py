"""
Train ML Trading Model
Run this first to train the model on historical data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml_trading_system import MLTradingSystem

def main():
    print("="*70)
    print("ML TRADING MODEL TRAINING")
    print("="*70)
    
    # Create ML system for ETH/USDT
    print("\n1. Setting up ML system for ETH/USDT...")
    ml_system = MLTradingSystem(symbol='ETH/USDT:USDT', timeframe='15m')
    
    # Train model
    print("\n2. Starting training (this may take 10-30 minutes)...")
    print("   Fetching 5000 candles of historical data...")
    print("   Engineering technical features...")
    print("   Training LSTM neural network...")
    print("   " + "-"*70)
    
    success = ml_system.train(epochs=50, batch_size=32)
    
    if success:
        print("\n" + "="*70)
        print("TRAINING COMPLETE!")
        print("="*70)
        print("\nModel saved to: ml_trading_model.h5")
        print("Scaler saved to: ml_scaler.pkl")
        print("Features saved to: ml_features.json")
        print("\nNext steps:")
        print("1. Test prediction: python ml_trading_bot.py")
        print("2. Start live trading: Edit ml_trading_bot.py and run bot.run_trading_loop()")
        
    else:
        print("\nTraining failed. Check errors above.")
        print("\nPossible issues:")
        print("- Not enough historical data (need 5000+ candles)")
        print("- API connection issues")
        print("- Missing dependencies (run: pip install -r ml_requirements.txt)")

if __name__ == "__main__":
    main()
