"""
Manual scan for high-confidence trading opportunities
"""

import ccxt
import time

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

PAIRS = [
    'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT',
    'DOGE/USDT:USDT', 'XRP/USDT:USDT', 'LINK/USDT:USDT', 'AVAX/USDT:USDT',
    'DOT/USDT:USDT', 'LTC/USDT:USDT', 'BCH/USDT:USDT', 'UNI/USDT:USDT',
    'ATOM/USDT:USDT', 'ETC/USDT:USDT', 'ARB/USDT:USDT', 'OP/USDT:USDT',
    'NEAR/USDT:USDT', 'APT/USDT:USDT', 'SUI/USDT:USDT'
]

print('=' * 60)
print('SCANNING FOR HIGH-CONFIDENCE OPPORTUNITIES (80%+)')
print('=' * 60)

signals_found = []

for symbol in PAIRS:
    try:
        # Fetch OHLCV
        ohlcv = exchange.fetch_ohlcv(symbol, '15m', limit=50)
        
        if len(ohlcv) < 30:
            continue
        
        closes = [c[4] for c in ohlcv]
        highs = [c[2] for c in ohlcv]
        lows = [c[3] for c in ohlcv]
        
        current = closes[-1]
        
        # RSI
        gains = []
        losses = []
        for i in range(1, 15):
            change = closes[-i] - closes[-(i+1)]
            gains.append(max(change, 0))
            losses.append(abs(min(change, 0)))
        
        avg_gain = sum(gains) / 14
        avg_loss = sum(losses) / 14
        rsi = 100 if avg_loss == 0 else 100 - (100 / (1 + avg_gain / avg_loss))
        
        # Trend
        sma20 = sum(closes[-20:]) / 20
        sma50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else sma20
        
        # Support/Resistance
        support = sorted(lows[-20:], reverse=True)[:3]
        resistance = sorted(highs[-20:])[:3]
        
        # Signals
        if rsi < 65 and rsi > 40 and current > sma20:
            if support and abs(current - max(support)) / current < 0.01:
                confidence = 80 + (65 - rsi) * 0.5
                signals_found.append({
                    'symbol': symbol,
                    'signal': 'LONG',
                    'confidence': min(confidence, 99),
                    'price': current,
                    'rsi': rsi
                })
        
        elif rsi > 35 and rsi < 60 and current < sma20:
            if resistance and abs(min(resistance) - current) / current < 0.01:
                confidence = 80 + (rsi - 35) * 0.5
                signals_found.append({
                    'symbol': symbol,
                    'signal': 'SHORT',
                    'confidence': min(confidence, 99),
                    'price': current,
                    'rsi': rsi
                })
                
    except Exception as e:
        pass

# Sort by confidence
signals_found.sort(key=lambda x: x['confidence'], reverse=True)

if signals_found:
    print(f"\nFound {len(signals_found)} signals:\n")
    for sig in signals_found:
        print(f"  {sig['symbol']}: {sig['signal']} ({sig['confidence']:.1f}%) | RSI: {sig['rsi']:.1f} | Price: ${sig['price']:.4f}")
else:
    print("\nNo 80%+ confidence signals found at this time.")

print('\n' + '=' * 60)
print('Auto-trader will open positions automatically when signals appear')
print('=' * 60)
