"""
Quick scan for entry signals across all strategies
Trade amount: $50
"""
import ccxt
import pandas as pd
import numpy as np
import talib
from datetime import datetime
import sys
import os

# Add parent dir for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============ CONFIGURATION ============
SYMBOLS = [
    'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 
    'DOGE/USDT:USDT', 'XRP/USDT:USDT', 'ADA/USDT:USDT',
    'LINK/USDT:USDT', 'DOT/USDT:USDT', 'LTC/USDT:USDT',
    'AVAX/USDT:USDT', 'MATIC/USDT:USDT'
]

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {msg}")

def get_exchange():
    """Initialize Bybit exchange"""
    try:
        exchange = ccxt.bybit({
            'apiKey': 'bsK06QDhsagOWwFsXQ',
            'secret': 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa',
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
        exchange.load_markets()
        return exchange
    except Exception as e:
        log(f"[ERR] Exchange error: {e}")
        return None

def fetch_ohlcv(exchange, symbol, timeframe, limit=50):
    """Fetch OHLCV data"""
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df
    except Exception as e:
        return None

def mean_reversion_signal(df):
    """Check for mean reversion signals (BB + RSI)"""
    if df is None or len(df) < 50:
        return None, 0
    
    close = df['close'].values
    rsi = talib.RSI(close, timeperiod=14)
    upper, middle, lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)
    
    if len(rsi) < 2 or len(upper) < 2:
        return None, 0
    
    current_rsi = rsi[-1]
    bb_pos = (close[-1] - lower[-1]) / (upper[-1] - lower[-1]) if upper[-1] != lower[-1] else 0.5
    
    # Long signal: RSI oversold + near lower band
    if current_rsi < 35 and bb_pos < 0.3:
        confidence = min(100, (35 - current_rsi) * 2 + (0.3 - bb_pos) * 100)
        return 'LONG', confidence
    
    # Short signal: RSI overbought + near upper band
    if current_rsi > 65 and bb_pos > 0.7:
        confidence = min(100, (current_rsi - 65) * 2 + (bb_pos - 0.7) * 100)
        return 'SHORT', confidence
    
    return None, 0

def momentum_signal(df):
    """Check for momentum signals (EMA crossover + RSI)"""
    if df is None or len(df) < 30:
        return None, 0
    
    close = df['close'].values
    volume = df['volume'].values
    
    ema9 = talib.EMA(close, timeperiod=9)
    ema21 = talib.EMA(close, timeperiod=21)
    rsi = talib.RSI(close, timeperiod=14)
    
    if len(ema9) < 2 or len(rsi) < 2:
        return None, 0
    
    # Bullish crossover
    if ema9[-2] <= ema21[-2] and ema9[-1] > ema21[-1] and rsi[-1] > 50 and rsi[-1] < 70:
        vol_increase = volume[-1] > volume[-2] * 1.2 if len(volume) > 1 else False
        confidence = 60 + (10 if vol_increase else 0) + (rsi[-1] - 50) * 0.5
        return 'LONG', min(100, confidence)
    
    # Bearish crossover
    if ema9[-2] >= ema21[-2] and ema9[-1] < ema21[-1] and rsi[-1] < 50 and rsi[-1] > 30:
        vol_increase = volume[-1] > volume[-2] * 1.2 if len(volume) > 1 else False
        confidence = 60 + (10 if vol_increase else 0) + (50 - rsi[-1]) * 0.5
        return 'SHORT', min(100, confidence)
    
    return None, 0

def scalping_signal(df):
    """Check for scalping signals (1m RSI extremes)"""
    if df is None or len(df) < 20:
        return None, 0
    
    close = df['close'].values
    rsi = talib.RSI(close, timeperiod=7)
    
    if len(rsi) < 2:
        return None, 0
    
    current_rsi = rsi[-1]
    prev_rsi = rsi[-2]
    
    # RSI bounce from extreme oversold
    if prev_rsi < 30 and current_rsi > prev_rsi:
        confidence = min(100, (30 - prev_rsi) * 3 + (current_rsi - prev_rsi) * 5)
        return 'LONG', confidence
    
    # RSI pullback from extreme overbought
    if prev_rsi > 70 and current_rsi < prev_rsi:
        confidence = min(100, (prev_rsi - 70) * 3 + (prev_rsi - current_rsi) * 5)
        return 'SHORT', confidence
    
    return None, 0

def scan_market():
    """Scan all symbols for entry signals"""
    log("=" * 60)
    log("BYBIT ENTRY SIGNAL SCAN - Trade Amount: $50")
    log("=" * 60)
    
    exchange = get_exchange()
    if not exchange:
        log("[ERR] Failed to connect to exchange")
        return
    
    log("[OK] Connected to Bybit Futures")
    log("")
    
    # Track signals
    mean_rev_signals = []
    momentum_signals = []
    scalping_signals = []
    
    for symbol in SYMBOLS:
        try:
            # Mean Reversion (5m)
            df_5m = fetch_ohlcv(exchange, symbol, '5m', 50)
            signal, conf = mean_reversion_signal(df_5m)
            if signal and conf >= 75:
                price = df_5m['close'].iloc[-1]
                mean_rev_signals.append({
                    'symbol': symbol.replace('/USDT:USDT', ''),
                    'side': signal,
                    'confidence': conf,
                    'price': price,
                    'timeframe': '5m'
                })
            
            # Momentum (5m)
            signal, conf = momentum_signal(df_5m)
            if signal and conf >= 60:
                price = df_5m['close'].iloc[-1]
                momentum_signals.append({
                    'symbol': symbol.replace('/USDT:USDT', ''),
                    'side': signal,
                    'confidence': conf,
                    'price': price,
                    'timeframe': '5m'
                })
            
            # Scalping (1m)
            df_1m = fetch_ohlcv(exchange, symbol, '1m', 30)
            signal, conf = scalping_signal(df_1m)
            if signal and conf >= 70:
                price = df_1m['close'].iloc[-1]
                scalping_signals.append({
                    'symbol': symbol.replace('/USDT:USDT', ''),
                    'side': signal,
                    'confidence': conf,
                    'price': price,
                    'timeframe': '1m'
                })
                
        except Exception as e:
            pass
    
    # Display results
    log("📊 MEAN REVERSION SIGNALS (BB + RSI, 5m):")
    log("-" * 50)
    if mean_rev_signals:
        for s in sorted(mean_rev_signals, key=lambda x: -x['confidence']):
            log(f"  🎯 {s['symbol']} {s['side']} | Confidence: {s['confidence']:.1f}% | Price: ${s['price']:.4f}")
    else:
        log("  No signals found (need RSI<35 + BB lower touch for LONG, or RSI>65 + BB upper for SHORT)")
    
    log("")
    log("🚀 MOMENTUM SIGNALS (EMA Crossover + RSI, 5m):")
    log("-" * 50)
    if momentum_signals:
        for s in sorted(momentum_signals, key=lambda x: -x['confidence']):
            log(f"  🎯 {s['symbol']} {s['side']} | Confidence: {s['confidence']:.1f}% | Price: ${s['price']:.4f}")
    else:
        log("  No signals found (need EMA 9/21 crossover with RSI confirmation)")
    
    log("")
    log("⚡ SCALPING SIGNALS (RSI Extremes, 1m):")
    log("-" * 50)
    if scalping_signals:
        for s in sorted(scalping_signals, key=lambda x: -x['confidence']):
            log(f"  🎯 {s['symbol']} {s['side']} | Confidence: {s['confidence']:.1f}% | Price: ${s['price']:.4f}")
    else:
        log("  No signals found (need RSI<30 bounce for LONG, or RSI>70 pullback for SHORT)")
    
    log("")
    log("=" * 60)
    log(f"TOTAL SIGNALS: MeanRev={len(mean_rev_signals)}, Momentum={len(momentum_signals)}, Scalping={len(scalping_signals)}")
    log("=" * 60)
    
    # Summary
    all_signals = mean_rev_signals + momentum_signals + scalping_signals
    if all_signals:
        log("")
        log("💡 RECOMMENDED ACTIONS:")
        for s in sorted(all_signals, key=lambda x: -x['confidence'])[:3]:
            log(f"   • {s['symbol']} {s['side']} @ ${s['price']:.4f} ({s['timeframe']}, {s['confidence']:.0f}% conf)")

if __name__ == '__main__':
    scan_market()
