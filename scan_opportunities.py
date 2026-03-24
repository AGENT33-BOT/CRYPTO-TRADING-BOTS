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

symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT', 'DOGE/USDT:USDT',
           'XRP/USDT:USDT', 'LINK/USDT:USDT', 'AVAX/USDT:USDT', 'DOT/USDT:USDT',
           'LTC/USDT:USDT', 'BCH/USDT:USDT', 'UNI/USDT:USDT', 'ATOM/USDT:USDT', 'ETC/USDT:USDT',
           'ARB/USDT:USDT', 'OP/USDT:USDT', 'NEAR/USDT:USDT', 'APT/USDT:USDT', 'SUI/USDT:USDT']

print('=' * 70)
print('MARKET SCAN - HIGH CONFIDENCE OPPORTUNITIES')
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
        
        current = df.iloc[-1]
        price = current['close']
        ema_9 = current['ema_9']
        ema_21 = current['ema_21']
        ema_50 = current['ema_50']
        rsi = current['rsi']
        
        # Score signals
        bullish = 0
        if ema_9 > ema_21 > ema_50: bullish += 2
        if price > ema_9: bullish += 1
        if rsi > 50 and rsi < 70: bullish += 1
        if rsi < 30: bullish += 2  # Oversold bounce
        
        bearish = 0
        if ema_9 < ema_21 < ema_50: bearish += 2
        if price < ema_9: bearish += 1
        if rsi < 50 and rsi > 30: bearish += 1
        if rsi > 70: bearish += 2  # Overbought pullback
        
        if bullish >= 3 and rsi < 65:
            confidence = min(95, bullish * 20 + (30 - rsi if rsi < 30 else 0))
            opportunities.append({
                'symbol': symbol,
                'direction': 'LONG',
                'confidence': confidence,
                'price': price,
                'rsi': rsi,
                'strength': bullish
            })
        elif bearish >= 3 and rsi > 35:
            confidence = min(95, bearish * 20 + (rsi - 70 if rsi > 70 else 0))
            opportunities.append({
                'symbol': symbol,
                'direction': 'SHORT',
                'confidence': confidence,
                'price': price,
                'rsi': rsi,
                'strength': bearish
            })
    except Exception as e:
        pass

# Sort by confidence
opportunities.sort(key=lambda x: x['confidence'], reverse=True)

print(f'\nFound {len(opportunities)} opportunities:\n')
for opp in opportunities[:10]:
    marker = '[LONG]' if opp['direction'] == 'LONG' else '[SHORT]'
    print(f"{marker} {opp['symbol']}")
    print(f"   Direction: {opp['direction']}")
    print(f"   Confidence: {opp['confidence']:.1f}%")
    print(f"   Price: ${opp['price']:.4f}")
    print(f"   RSI: {opp['rsi']:.1f}")
    print(f"   Strength: {opp['strength']}/5")
    print()

# Show 90%+ opportunities
high_conf = [o for o in opportunities if o['confidence'] >= 90]
print('=' * 70)
print(f'HIGH CONFIDENCE (90%+) OPPORTUNITIES: {len(high_conf)}')
print('=' * 70)
for opp in high_conf:
    print(f"{opp['symbol']} | {opp['direction']} | {opp['confidence']:.1f}% | RSI: {opp['rsi']:.1f}")
