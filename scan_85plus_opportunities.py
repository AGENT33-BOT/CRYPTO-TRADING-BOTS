import ccxt
import pandas as pd
import numpy as np

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

# Expanded symbol list - all available pairs
symbols = [
    'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT', 
    'DOGE/USDT:USDT', 'XRP/USDT:USDT', 'LINK/USDT:USDT', 'AVAX/USDT:USDT',
    'DOT/USDT:USDT', 'LTC/USDT:USDT', 'BCH/USDT:USDT', 'UNI/USDT:USDT',
    'ATOM/USDT:USDT', 'ETC/USDT:USDT', 'ARB/USDT:USDT', 'OP/USDT:USDT',
    'NEAR/USDT:USDT', 'APT/USDT:USDT', 'SUI/USDT:USDT', 'FIL/USDT:USDT',
    'TRX/USDT:USDT', 'MATIC/USDT:USDT', 'ALGO/USDT:USDT', 'VET/USDT:USDT',
    'ICP/USDT:USDT', 'MANA/USDT:USDT', 'SAND/USDT:USDT', 'AXS/USDT:USDT'
]

print('=' * 70)
print('COMPREHENSIVE SCAN - 85%+ CONFIDENCE')
print('=' * 70)

opportunities = []
for symbol in symbols:
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, '15m', limit=50)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # EMAs
        df['ema_9'] = df['close'].ewm(span=9).mean()
        df['ema_21'] = df['close'].ewm(span=21).mean()
        df['ema_50'] = df['close'].ewm(span=50).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # ATR for volatility
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['atr'] = true_range.rolling(14).mean()
        
        # Bollinger Bands
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['std_20'] = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['sma_20'] + (df['std_20'] * 2)
        df['bb_lower'] = df['sma_20'] - (df['std_20'] * 2)
        
        current = df.iloc[-1]
        price = current['close']
        ema_9 = current['ema_9']
        ema_21 = current['ema_21']
        ema_50 = current['ema_50']
        rsi = current['rsi']
        atr = current['atr']
        bb_upper = current['bb_upper']
        bb_lower = current['bb_lower']
        
        # Skip if not enough data
        if pd.isna(ema_50):
            continue
        
        # Enhanced scoring system
        bullish_score = 0
        bearish_score = 0
        
        # Trend alignment (0-2 points)
        if ema_9 > ema_21 > ema_50:
            bullish_score += 2
        elif ema_9 > ema_21:
            bullish_score += 1
        elif ema_9 < ema_21 < ema_50:
            bearish_score += 2
        elif ema_9 < ema_21:
            bearish_score += 1
        
        # Price vs EMA (0-1 point)
        if price > ema_9:
            bullish_score += 1
        elif price < ema_9:
            bearish_score += 1
        
        # RSI momentum (0-2 points)
        if 30 <= rsi < 40:  # Oversold bounce potential
            bullish_score += 2
        elif 40 <= rsi < 50:
            bullish_score += 1
        elif 60 < rsi <= 70:  # Overbought pullback potential
            bearish_score += 2
        elif 50 < rsi <= 60:
            bearish_score += 1
        
        # Volume trend
        recent_volume = df['volume'].tail(5).mean()
        older_volume = df['volume'].tail(10).head(5).mean()
        if recent_volume > older_volume * 1.2:
            if bullish_score > bearish_score:
                bullish_score += 1
            elif bearish_score > bullish_score:
                bearish_score += 1
        
        # Calculate confidence (max 100)
        max_possible = 6  # Maximum possible raw score
        
        if bullish_score >= 4 and rsi < 65:
            confidence = min(95, int((bullish_score / max_possible) * 100) + (40 - rsi if rsi < 40 else 0))
            if confidence >= 85:
                opportunities.append({
                    'symbol': symbol,
                    'direction': 'LONG',
                    'confidence': confidence,
                    'price': price,
                    'rsi': rsi,
                    'atr': atr,
                    'score': bullish_score
                })
        
        if bearish_score >= 4 and rsi > 35:
            confidence = min(95, int((bearish_score / max_possible) * 100) + (rsi - 60 if rsi > 60 else 0))
            if confidence >= 85:
                opportunities.append({
                    'symbol': symbol,
                    'direction': 'SHORT',
                    'confidence': confidence,
                    'price': price,
                    'rsi': rsi,
                    'atr': atr,
                    'score': bearish_score
                })
    except Exception as e:
        pass

# Sort by confidence
opportunities.sort(key=lambda x: x['confidence'], reverse=True)

print(f'\nFound {len(opportunities)} opportunities (85%+):\n')
for opp in opportunities[:15]:
    marker = '[LONG]' if opp['direction'] == 'LONG' else '[SHORT]'
    print(f"{marker} {opp['symbol']}")
    print(f"   Direction: {opp['direction']}")
    print(f"   Confidence: {opp['confidence']}%")
    print(f"   Price: ${opp['price']:.4f}")
    print(f"   RSI: {opp['rsi']:.1f}")
    print(f"   ATR: ${opp['atr']:.4f}" if not pd.isna(opp['atr']) else "   ATR: N/A")
    print(f"   Score: {opp['score']}/6")
    print()

# Show 90%+ opportunities
high_conf = [o for o in opportunities if o['confidence'] >= 90]
print('=' * 70)
print(f'HIGH CONFIDENCE (90%+) OPPORTUNITIES: {len(high_conf)}')
print('=' * 70)
for opp in high_conf:
    print(f"{opp['symbol']} | {opp['direction']} | {opp['confidence']:.0f}% | RSI: {opp['rsi']:.1f}")

# Show 85-89% opportunities  
med_conf = [o for o in opportunities if 85 <= o['confidence'] < 90]
print('=' * 70)
print(f'GOOD CONFIDENCE (85-89%) OPPORTUNITIES: {len(med_conf)}')
print('=' * 70)
for opp in med_conf:
    print(f"{opp['symbol']} | {opp['direction']} | {opp['confidence']:.0f}% | RSI: {opp['rsi']:.1f}")
