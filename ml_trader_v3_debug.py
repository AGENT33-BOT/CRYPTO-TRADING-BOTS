"""
ML Trader v3 - Maximum Debug Version
"""

import ccxt
import pandas as pd
import numpy as np
import talib
import pickle
import time
from datetime import datetime

print(f"\n{'='*60}")
print(f"ML TRADER v3 - DEBUG MODE")
print(f"{'='*60}\n")

# Config - HARDCODED
SYMBOL = 'ETH/USDT:USDT'
RISK_PER_TRADE = 0.10  # 10%
MIN_CONFIDENCE = 0.65
LEVERAGE = 3

print(f"Symbol: {SYMBOL}")
print(f"Risk: {RISK_PER_TRADE:.0%}")
print(f"Min Confidence: {MIN_CONFIDENCE:.0%}")
print()

# Init exchange
exchange = ccxt.bybit({
    'apiKey': 'bsK06QDhsagOWwFsXQ',
    'secret': 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa',
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})
exchange.set_sandbox_mode(False)

# Load model
safe_symbol = SYMBOL.replace('/', '_')
with open(f'rf_model_{safe_symbol}.pkl', 'rb') as f:
    model = pickle.load(f)
with open(f'rf_scaler_{safe_symbol}.pkl', 'rb') as f:
    scaler = pickle.load(f)
with open(f'rf_features_{safe_symbol}.txt', 'r') as f:
    features = f.read().strip().split('\n')

print("Model loaded!")
print(f"Features: {features}")
print()

def get_balance():
    balance = exchange.fetch_balance()
    return balance['USDT']['free']

def get_position():
    positions = exchange.fetch_positions([SYMBOL])
    for pos in positions:
        if abs(float(pos['contracts'])) > 0:
            return pos
    return None

def calculate_position_size(confidence, balance):
    """Calculate with full debug"""
    print(f"  Balance: ${balance:.2f}")
    
    target_usd = balance * RISK_PER_TRADE * confidence
    print(f"  Target (10% x {confidence:.0%} conf): ${target_usd:.2f}")
    
    # Get price
    ticker = exchange.fetch_ticker(SYMBOL)
    price = ticker['last']
    print(f"  {SYMBOL} price: ${price:.2f}")
    
    # ETH: 1 contract = 0.01 ETH
    usd_per_contract = price * 0.01
    print(f"  USD per contract: ${usd_per_contract:.2f}")
    
    contracts = int(target_usd / usd_per_contract)
    print(f"  Raw contracts: {contracts}")
    
    # Minimum
    contracts = max(contracts, 1)
    print(f"  After min(1): {contracts}")
    
    actual_usd = contracts * usd_per_contract
    print(f"  Actual USD: ${actual_usd:.2f}")
    
    return contracts

# Main loop
while True:
    try:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scanning {SYMBOL}...")
        
        # Check position
        pos = get_position()
        if pos:
            print(f"  Current position: {pos['contracts']} {pos['side']}")
        else:
            print(f"  No position - FLAT")
        
        # Get prediction
        ohlcv = exchange.fetch_ohlcv(SYMBOL, '15m', limit=50)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['returns'] = df['close'].pct_change()
        df['rsi'] = talib.RSI(df['close'].values, timeperiod=14)
        df['macd'], _, _ = talib.MACD(df['close'].values)
        
        latest = df[features].iloc[-1].values.reshape(1, -1)
        latest_scaled = scaler.transform(latest)
        
        prediction = model.predict(latest_scaled)[0]
        probabilities = model.predict_proba(latest_scaled)[0]
        confidence = max(probabilities)
        
        signal = 'UP' if prediction == 1 else 'DOWN'
        print(f"  Signal: {signal} | Confidence: {confidence:.2%}")
        
        if confidence >= MIN_CONFIDENCE and not pos:
            print(f"  HIGH CONFIDENCE - EXECUTING TRADE!")
            balance = get_balance()
            size = calculate_position_size(confidence, balance)
            
            if signal == 'UP':
                print(f"  Creating BUY order: {size} contracts")
                order = exchange.create_market_buy_order(SYMBOL, size)
            else:
                print(f"  Creating SELL order: {size} contracts")
                order = exchange.create_market_sell_order(SYMBOL, size)
            
            print(f"  Order ID: {order['id']}")
            print(f"  TRADE EXECUTED!")
        else:
            if pos:
                print(f"  Already in position - skipping")
            else:
                print(f"  Confidence too low ({confidence:.2%} < {MIN_CONFIDENCE:.0%}) - no trade")
        
        print(f"  Sleeping 15 min...")
        time.sleep(15 * 60)
        
    except Exception as e:
        print(f"  ERROR: {e}")
        time.sleep(60)
